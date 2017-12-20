import collections
import copy
import re

import pymongo.errors

from . import manager
from .exceptions import ValidationError
from .fields import ModelField, Id
from .router import databases


class MetaModel(type):

    errors = {
        'unique': 'Value must be unique'
    }

    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return collections.OrderedDict()

    def __new__(mcs, name, bases, attributes):
        fields = collections.OrderedDict()

        for parent in bases:
            if hasattr(parent, 'Meta'):
                fields.update(parent.Meta.fields)

        attributes['_id'] = Id(required=False, read_only=True)
        attributes.move_to_end('_id', last=False)

        for key, value in list(attributes.items()):
            if isinstance(value, ModelField):
                value.bind(name=key)
                fields[key] = value
                attributes.pop(key, None)

        attributes.setdefault('Meta', type('Meta', (), {}))

        cls = super().__new__(mcs, name, bases, attributes)

        for field in fields.values():
            field.bind(model=cls)

        cls.ValidationError = ValidationError
        cls.DoesNotExist = type('DoesNotExist', (Exception,), {})

        cls.objects = getattr(cls.Meta, 'objects', manager.Manager())
        cls.objects.bind(model=cls)

        cls.Meta.fields = fields

        if hasattr(cls.Meta, 'collection'):
            alias = getattr(cls.Meta, 'database', 'default')
            cls.Meta.collection = databases.get(alias)[cls.Meta.collection]

        errors = mcs.errors.copy()
        errors.update(getattr(cls.Meta, 'errors', {}))
        cls.Meta.errors = errors

        return cls


class Model(object, metaclass=MetaModel):

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        self.Meta = cls.Meta()
        return self

    def __init__(self, **kwargs):
        self.Meta.data = kwargs

    def __getattr__(self, attribute):
        if attribute in self.Meta.fields:
            field = self.Meta.fields[attribute]
            return self.Meta.data.get(attribute, field.default)

        raise AttributeError(attribute)

    def __setattr__(self, attribute, value):
        if attribute in self.Meta.fields:
            self.Meta.data[attribute] = value
        else:
            return super().__setattr__(attribute, value)

    def __str__(self):
        return '{} object'.format(self.__class__.__name__)

    def __eq__(self, other):
        return self._id == other._id

    @classmethod
    async def get_options(cls):
        metadata = []

        for field in cls.Meta.fields.values():
            metadata.append(await field.get_options())

        return metadata

    @classmethod
    def using(cls, *, database='default', collection=None):
        database = databases.get(database)
        collection = database[collection or cls.Meta.collection.name]
        model = copy.deepcopy(cls)

        model.Meta.collection = collection
        model.objects.bind(model=model)

        return model

    def fail(self, code, field):
        raise self.ValidationError({field: self.Meta.errors[code]})

    @classmethod
    async def from_db(cls, data, raw_fields=()):
        for name, field in cls.Meta.fields.items():
            value = data.get(name)

            if value is None or name in raw_fields:
                data[name] = value
            else:
                try:
                    data[name] = await field.db_deserialize(value)
                except cls.ValidationError:
                    data[name] = None

        instance = cls(**data)
        instance.Meta.raw_fields = raw_fields

        return instance

    @classmethod
    async def prepare(cls):
        for name, field in cls.Meta.fields.items():
            if field.index is not None:
                await cls.Meta.collection.create_index(
                    ((name, field.index),),
                    unique=field.unique,
                    sparse=True,
                    background=True
                )

    async def deserialize(self):
        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name, field.default)

            if value is not None:
                value = await field.deserialize(value)

            self.Meta.data[name] = value

        return self

    async def serialize(self):
        data = {}

        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if value is None:
                data[name] = value
            else:
                data[name] = await field.serialize(value)

        return data

    async def db_serialize(self):
        data = {}

        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if value is not None:
                data[name] = await field.db_serialize(value)

        return data

    async def validate(self):
        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if field.read_only and name != '_id':
                value = field.default

            try:
                value = await field.validate(value)
            except self.ValidationError as e:
                raise self.ValidationError({name: e.error})

            self.Meta.data[name] = value

        self.Meta.raw_fields = ()
        return self

    async def on_save(self):
        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)
            self.Meta.data[name] = await field.on_save(value)

    async def on_create(self):
        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)
            self.Meta.data[name] = await field.on_create(value)

    async def save(self, force=False):
        if not self._id:
            await self.on_create()

        await self.on_save()

        if not force:
            await self.validate()

        data = await self.db_serialize()
        data.pop('_id', None)

        try:
            if self._id:
                await self.Meta.collection.update({'_id': self._id}, data)
            else:
                self.Meta.data['_id'] = await self.Meta.collection.insert(data)
        except pymongo.errors.DuplicateKeyError as e:
            field = re.search(r'\$?(\w+)_\d+', str(e)).group(1)
            self.fail('unique', field)

        return self

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            self.Meta.data[key] = value

        return await self.save()

    async def refresh(self):
        if self._id:
            data = await self.Meta.collection.find_one({'_id': self._id})
            self.Meta.data.update(data)
            return await self.deserialize()

    async def delete(self):
        if self._id:
            await self.Meta.collection.remove({'_id': self._id})
