# coding=utf-8

import collections

from . import exceptions
from .fields import Field


class MetaForm(type):

    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return collections.OrderedDict()

    def __new__(mcs, name, bases, attributes):
        fields = collections.OrderedDict()

        for parent in bases:
            if hasattr(parent, '__fields__'):
                fields.update(parent.__fields__)

        for key, value in attributes.items():
            if isinstance(value, Field):
                fields[key] = value

        for field in fields:
            attributes.pop(field, None)

        cls = type.__new__(mcs, name, bases, attributes)

        cls.__fields__ = fields
        cls.ValidationError = exceptions.ValidationError

        for name, field in cls.__fields__.items():
            field.bind(name=name)

        return cls


class Form(object, metaclass=MetaForm):

    def __init__(self, *, instance=None, data=None):
        self.__instance__ = instance
        self.__values__ = {name: None for name in self.__fields__.keys()}

        if self.__instance__ is not None:
            for name in self.__fields__.keys():
                self.__values__[name] = getattr(self.__instance__, name, None)

        if data is not None:
            for name in self.__fields__.keys():
                self.__values__[name] = data.get(name, self.__values__[name])

    def __getattr__(self, attribute):
        if attribute in self.__fields__:
            field = self.__fields__[attribute]
            return self.__values__.get(attribute, field.default)

        raise AttributeError(attribute)

    def __setattr__(self, attribute, value):
        if attribute in self.__fields__:
            self.__values__[attribute] = value
        else:
            return super().__setattr__(attribute, value)

    @classmethod
    async def get_options(cls):
        metadata = []

        for field in cls.__fields__.values():
            metadata.append(await field.get_options())

        return metadata

    def get_values(self):
        values = {}

        for name in self.__fields__:
            values[name] = self.__values__.get(name)

            if name == '_id':
                values[name] = str(values[name])

        return values

    async def to_python(self):
        for name, field in self.__fields__.items():
            value = self.__values__.get(name)

            if value is None:
                self.__values__[name] = field.default
                continue

            try:
                self.__values__[name] = await field.to_python(value)
            except exceptions.ValidationError:
                self.__values__[name] = field.default

        return self

    async def validate(self):
        self.__errors__ = {}

        for name, field in self.__fields__.items():
            value = self.__values__.get(name)

            try:
                if field.read_only and not self.__instance__:
                    if not (value is None or value == field.default):
                        field.fail('read_only')

                self.__values__[name] = await field.validate(value, self)
            except exceptions.ValidationError as e:
                self.__errors__[name] = e.error

        if self.__errors__:
            raise exceptions.ValidationError(self.__errors__)

        return self

    async def serialize(self):
        data = {}

        for name, field in self.__fields__.items():
            value = self.__values__.get(name)

            if value is not None:
                data[name] = await field.to_internal_value(value)
            else:
                data[name] = None

        return data

    async def save(self):
        pass
