# coding=utf-8

import tornado.gen

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
            self.__collection__ and db.get_database()[self.__collection__]
        )

    @tornado.gen.coroutine
    def serialize(self):
        data = yield super().serialize()
        data['_id'] = data['_id'] and str(data['_id'])
        return data

    @tornado.gen.coroutine
    def save(self):
        data = yield self.validate()
        data.pop('_id')

        if self._id:
            yield self.__cursor__.update({'_id': self._id}, data)
        else:
            self.__values__['_id'] = yield self.__cursor__.insert(data)

        yield self.construct()

        return self

    @tornado.gen.coroutine
    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__values__[key] = value

        yield self.save()

    @tornado.gen.coroutine
    def refresh(self):
        if self._id:
            data = yield self.__cursor__.find_one({'_id': self._id})

            self.__values__.update(data)

            yield self.construct()

    @tornado.gen.coroutine
    def delete(self):
        if self._id:
            print(self._id)
            yield self.__cursor__.remove({'_id': self._id})

    def __str__(self):
        return '{} object'.format(self.__class__.__name__)
