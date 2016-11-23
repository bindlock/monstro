# coding=utf-8

from monstro.forms.forms import Form, MetaForm

from . import manager, db
from .exceptions import DoesNotExist
from .fields import Id


class MetaModel(MetaForm):

    def __new__(mcs, name, bases, attributes):
        if '_id' in attributes:
            raise AttributeError('Field "_id" reserved')

        attributes['_id'] = Id(required=False, read_only=True)
        attributes.move_to_end('_id', last=False)

        cls = super().__new__(mcs, name, bases, attributes)

        if attributes.get('__collection__') is not None:
            cls.objects = attributes.get('objects', manager.Manager())
            cls.objects.bind(model=cls)

        cls.DoesNotExist = DoesNotExist

        for name, field in cls.__fields__.items():
            field.bind(model=cls)

        return cls


class Model(Form, metaclass=MetaModel):

    __collection__ = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__instance__ = self.__instance__ or self
        self.__cursor__ = (
            self.__collection__ and db.database[self.__collection__]
        )

    def __str__(self):
        return '{} object'.format(self.__class__.__name__)

    def __eq__(self, other):
        return self._id == other._id

    async def to_db_value(self):
        data = {}

        for name, field in self.__fields__.items():
            value = self.__values__.get(name)

            if name in self.__raw_fields__:
                data[name] = value
                continue

            if value is not None:
                data[name] = await field.to_db_value(value)
            else:
                data[name] = None

        return data

    async def on_save(self):
        for name, field in self.__fields__.items():
            value = self.__values__.get(name)
            self.__values__[name] = await field.on_save(value)

    async def on_create(self):
        for name, field in self.__fields__.items():
            value = self.__values__.get(name)
            self.__values__[name] = await field.on_create(value)

    async def save(self, force=False):
        if not self._id:
            await self.on_create()

        await self.on_save()

        if not force:
            await self.validate()

        data = await self.to_db_value()
        data.pop('_id')

        if self._id:
            await self.__cursor__.update({'_id': self._id}, data)
        else:
            self.__values__['_id'] = await self.__cursor__.insert(data)

        return self

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__values__[key] = value

        return await self.save()

    async def refresh(self):
        if self._id:
            data = await self.__cursor__.find_one({'_id': self._id})
            self.__values__.update(data)
            return await self.deserialize()

    async def delete(self):
        if self._id:
            await self.__cursor__.remove({'_id': self._id})
