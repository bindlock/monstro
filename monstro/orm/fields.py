# coding=utf-8

import bson.errors
from bson.objectid import ObjectId
from tornado.util import import_object

from monstro.forms import widgets
from monstro.forms.fields import *  # pylint: disable=W0401,W0614

from .exceptions import InvalidQuery


__all__ = (
    'Id',
    'ForeignKey',
    'ManyToMany'
)


class Id(Field):

    widget = widgets.Input('hidden')
    error_messages = {
        'invalid': 'Value must be an valid MongoDB Id'
    }

    def __init__(self, **kwargs):
        kwargs['required'] = False
        super().__init__(**kwargs)

    async def to_python(self, value):
        if isinstance(value, str):
            try:
                return ObjectId(value)
            except bson.errors.InvalidId:
                self.fail('invalid')
        elif not isinstance(value, ObjectId):
            self.fail('invalid')

        return value

    async def to_internal_value(self, value):
        return str(value)


class ForeignKey(Field):

    error_messages = {
        'invalid': 'Model instance must be a {0.to.__name__}',
        'foreign_key': 'Related model not found'
    }

    def __init__(self, *, to, to_field='_id', **kwargs):
        super().__init__(**kwargs)

        self.to = to
        self.to_field = to_field

    def get_related_model(self):
        if isinstance(self.to, str):
            if self.to == 'self':
                self.to = self.model
            else:
                self.to = import_object(self.to)

        return self.to

    async def to_python(self, value):
        model = self.get_related_model()

        if isinstance(value, model):
            if not value._id:
                self.fail('foreign_key')

            return value
        elif isinstance(value, str) and self.to_field == '_id':
            try:
                value = ObjectId(value)
            except bson.errors.InvalidId:
                self.fail('invalid')

        query = {self.to_field: value}

        try:
            value = await model.objects.get(**query)
        except model.DoesNotExist:
            self.fail('foreign_key')
        except (bson.errors.InvalidDocument, InvalidQuery):
            self.fail('invalid')

        return value

    async def to_internal_value(self, value):
        value = getattr(value, self.to_field)

        if self.to_field == '_id':
            return str(value)

        return value

    async def get_options(self):
        choices = []
        model = self.get_related_model()

        async for item in model.objects.values():
            instance = model(data=item)

            try:
                choices.append((str(item[self.to_field]), str(instance)))
            except (AttributeError, KeyError):
                await instance.to_python()
                choices.append((str(item[self.to_field]), str(instance)))

        self.widget = widgets.Select(choices)

        return await super().get_options()


class ManyToMany(Array):

    def __init__(self, **kwargs):
        super().__init__(field=ForeignKey(**kwargs))  # pylint: disable=E1125

    async def get_options(self):
        options = await super().get_options()

        widget = (await self.field.get_options())['widget']
        widget['attrs']['multiple'] = 'multiple'
        options['widget'] = widget

        return options
