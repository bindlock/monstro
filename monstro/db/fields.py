import datetime

from bson.objectid import ObjectId
from tornado.util import import_object
import bson.errors
import pymongo

from monstro.forms import fields, widgets

from .exceptions import InvalidQuery


__all__ = (
    'Boolean',
    'String',
    'Integer',
    'Float',
    'Choice',
    'Array',
    'MultipleChoice',
    'URL',
    'RegexMatch',
    'Host',
    'Slug',
    'Map',
    'JSON',
    'Date',
    'Time',
    'DateTime',
    'PythonPath',
    'RegularExpression',
    'Id',
    'ForeignKey',
    'ManyToMany',
)


class ModelField(object):

    def __init__(self, *, unique=False, index=None, **kwargs):
        super().__init__(**kwargs)

        self.unique = unique
        self.index = index

        if self.unique:
            self.index = pymongo.ASCENDING

        self.model = None

    async def db_deserialize(self, value):
        return await self.deserialize(value)

    async def db_serialize(self, value):
        return await self.serialize(value)

    async def on_save(self, value):
        return value

    async def on_create(self, value):
        return value


class String(ModelField, fields.String):

    pass


class Boolean(ModelField, fields.Boolean):

    pass


class Integer(ModelField, fields.Integer):

    pass


class Float(ModelField, fields.Float):

    pass


class Choice(ModelField, fields.Choice):

    pass


class Array(ModelField, fields.Array):

    pass


class MultipleChoice(ModelField, fields.MultipleChoice):  # pylint:disable=R0901

    pass


class URL(ModelField, fields.URL):

    pass


class RegexMatch(ModelField, fields.RegexMatch):

    pass


class Host(ModelField, fields.Host):  # pylint:disable=R0901

    pass


class Slug(ModelField, fields.Slug):  # pylint:disable=R0901

    pass


class Map(ModelField, fields.Map):

    pass


class JSON(ModelField, fields.JSON):

    pass


class DateTime(ModelField, fields.DateTime):

    async def db_serialize(self, value):
        return value

    async def db_deserialize(self, value):
        return value

    async def on_save(self, value):
        if self.auto_now:
            return datetime.datetime.utcnow()

        return value

    async def on_create(self, value):
        if self.auto_now_on_create:
            return datetime.datetime.utcnow()

        return value


class Date(DateTime, fields.Date):

    pass


class Time(DateTime, fields.Time):

    pass


class PythonPath(ModelField, fields.PythonPath):

    pass


class RegularExpression(ModelField, fields.RegularExpression):

    pass


class Id(ModelField, fields.Field):

    widget = widgets.Input('hidden')
    errors = {
        'invalid': 'Value must be an valid MongoDB Id'
    }

    def __init__(self, **kwargs):
        kwargs['required'] = False
        super().__init__(**kwargs)

    async def deserialize(self, value):
        if isinstance(value, str):
            try:
                return ObjectId(value)
            except bson.errors.InvalidId:
                self.fail('invalid')
        elif not isinstance(value, ObjectId):
            self.fail('invalid')

        return value

    async def serialize(self, value):
        return str(value)


class ForeignKey(ModelField, fields.Field):

    errors = {
        'invalid': 'Model instance must be a {0.to.__name__}',
        'foreign_key': 'Related model not found'
    }

    def __init__(self, *, to, to_field='_id', **kwargs):
        kwargs.setdefault('index', pymongo.ASCENDING)
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

    async def deserialize(self, value):
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

    async def serialize(self, value):
        value = getattr(value, self.to_field)

        if self.to_field == '_id':
            return str(value)

        return value

    async def get_options(self):
        choices = []
        model = self.get_related_model()

        async for item in model.objects.values():
            instance = model(**item)

            try:
                choices.append((str(item[self.to_field]), str(instance)))
            except (AttributeError, KeyError):
                await instance.deserialize()
                choices.append((str(item[self.to_field]), str(instance)))

        self.widget = widgets.Select(choices)

        return await super().get_options()


class ManyToMany(ModelField, fields.Array):

    def __init__(self, *, to, to_field='_id', **kwargs):
        field = ForeignKey(to=to, to_field=to_field)
        super().__init__(field=field, **kwargs)

    async def get_options(self):
        options = await super().get_options()

        widget = (await self.field.get_options())['widget']
        widget['attrs']['multiple'] = 'multiple'
        options['widget'] = widget

        return options
