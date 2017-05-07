import collections

from . import manager, db
from .exceptions import ValidationError
from .fields import ModelField, Id


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

        cls.ValidationError = ValidationError
        cls.DoesNotExist = type('DoesNotExist', (Exception,), {})

        cls.objects = getattr(cls.Meta, 'objects', manager.Manager())
        cls.objects.bind(model=cls)

        cls.Meta.fields = fields

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

        if hasattr(self.Meta, 'collection'):
            self.Meta.collection = db.database[self.Meta.collection]

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

    def fail(self, code, field):
        raise self.ValidationError({field: self.Meta.errors[code]})

    async def deserialize(self):
        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if value is None:
                value = field.default
            else:
                value = await field.deserialize(value)

            self.Meta.data[name] = value

        return self

    async def serialize(self):
        data = {}

        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if value is not None:
                data[name] = await field.serialize(value)
            else:
                data[name] = None

        return data

    async def db_serialize(self):
        data = {}

        for name, field in self.Meta.fields.items():
            value = self.Meta.data.get(name)

            if value is not None:
                data[name] = await field.db_serialize(value)
            else:
                data[name] = None

        return data

    async def validate(self):
        for name, field in self.Meta.fields.items():
            try:
                value = await field.validate(self.Meta.data.get(name))
            except self.ValidationError as e:
                raise self.ValidationError({name: e.error})

            if field.unique:
                try:
                    instance = await self.objects.get(**{name: value})
                except self.DoesNotExist:
                    pass
                else:
                    if not self._id or self._id != instance._id:
                        self.fail('unique', name)

            self.Meta.data[name] = value

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
        data.pop('_id')

        if self._id:
            await self.Meta.collection.update({'_id': self._id}, data)
        else:
            self.Meta.data['_id'] = await self.Meta.collection.insert(data)

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
