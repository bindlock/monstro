# coding=utf-8

import tornado.gen

from tornado.util import import_object
from bson.objectid import ObjectId
import bson.errors

from monstro.forms import widgets
from monstro.forms.fields import String, Field


class Id(String):

    widget = widgets.Input('hidden')
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
                return ObjectId(value)
            except bson.errors.InvalidId:
                return None

        return None

    @tornado.gen.coroutine
    def to_representation(self, value):
        return (yield self.to_internal_value(value))


class ForeignKey(Field):

    default_error_messages = {
        'invalid': 'Model instance must be a {0.related_model.__name__}',
        'foreign_key': 'Related model not found'
    }

    def __init__(self, *, related_model, related_field='_id', **kwargs):
        super().__init__(**kwargs)

        self.related_model = related_model
        self.related_field = related_field

    def get_related_model(self):
        if isinstance(self.related_model, str):
            if self.related_model == 'self':
                self.related_model = self.model
            else:
                self.related_model = import_object(self.related_model)

        return self.related_model

    @tornado.gen.coroutine
    def to_representation(self, value):
        related_model = self.get_related_model()

        if isinstance(value, str) or isinstance(value, ObjectId):
            if self.related_field == '_id' and isinstance(value, str):
                try:
                    value = ObjectId(value)
                except bson.errors.InvalidId:
                    return None

            query = {self.related_field: value}

            try:
                value = yield related_model.objects.get(**query)
            except self.related_model.DoesNotExist:
                return None

        return value

    @tornado.gen.coroutine
    def is_valid(self, value):
        related_model = self.get_related_model()

        if not (isinstance(value, str) or isinstance(value, ObjectId)):
            if not isinstance(value, related_model):
                self.fail('invalid')

            query = {self.related_field: getattr(value, self.related_field)}
        else:
            query = {self.related_field: value}

        try:
            value = yield related_model.objects.get(**query)
        except related_model.DoesNotExist:
            self.fail('foreign_key')

        return value

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        related_model = self.get_related_model()

        if not value or isinstance(value, str):
            return value
        elif not isinstance(value, related_model):
            return None

        value = getattr(value, self.related_field)

        if self.related_field == '_id':
            return str(value)

        return value

    @tornado.gen.coroutine
    def get_metadata(self):
        items = yield self.get_related_model().objects.all()
        choices = []

        for item in items:
            choices.append((str(getattr(item, self.related_field)), str(item)))

        self.widget = widgets.Select(choices)

        return (yield super().get_metadata())
