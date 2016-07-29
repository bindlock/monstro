# coding=utf-8

import tornado.gen

from tornado.util import import_object
from bson.objectid import ObjectId
import bson.errors

from monstro.ui import inputs
from monstro.serializers.fields import StringField, Field


class IDField(StringField):

    widget = inputs.Input('hidden')
    default_error_messages = {
        'invalid': 'Value must be an valid MongoDB Id'
    }

    def __init__(self, **kwargs):
        kwargs['required'] = False
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def is_valid(self, value):
        if isinstance(value, str):
            try:
                ObjectId(value)
            except bson.errors.InvalidId:
                self.fail('invalid')

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        if value is not None:
            try:
                raise tornado.gen.Return(ObjectId(value))
            except bson.errors.InvalidId:
                raise tornado.gen.Return(None)

        raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def to_representation(self, value):
        raise tornado.gen.Return((yield self.to_internal_value(value)))


class ForeignKeyField(Field):

    default_error_messages = {
        'invalid': 'Model instance must be a {0.related_model.__name__}',
        'foreign_key': 'Related model not found'
    }

    def __init__(self, *, related_model, related_field='_id', **kwargs):
        super().__init__(**kwargs)

        if isinstance(related_model, str):
            related_model = import_object(related_model)

        self.related_model = related_model
        self.related_field = related_field

    @tornado.gen.coroutine
    def to_representation(self, value):
        if isinstance(value, str) or isinstance(value, ObjectId):
            if self.related_field == '_id' and isinstance(value, str):
                try:
                    value = ObjectId(value)
                except bson.errors.InvalidId:
                    self.fail('foreign_key')

            query = {self.related_field: value}

            try:
                value = yield self.related_model.objects.get(**query)
            except self.related_model.DoesNotExist:
                self.fail('foreign_key')

        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def is_valid(self, value):
        if not isinstance(value, str):
            if not isinstance(value, self.related_model):
                self.fail('invalid')

            query = {self.related_field: getattr(value, self.related_field)}
        else:
            query = {self.related_field: value}

        try:
            value = yield self.related_model.objects.get(**query)
        except self.related_model.DoesNotExist:
            self.fail('foreign_key')

        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        if not value or isinstance(value, str):
            raise tornado.gen.Return(value)
        elif not isinstance(value, self.related_model):
            raise tornado.gen.Return(None)

        value = getattr(value, self.related_field)

        if self.related_field == '_id':
            raise tornado.gen.Return(str(value))

        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def get_metadata(self):
        items = yield self.related_model.objects.all()
        choices = []

        for item in items:
            choices.append((str(getattr(item, self.related_field)), str(item)))

        self.widget = inputs.Select(choices)

        raise tornado.gen.Return((yield super().get_metadata()))
