# coding=utf-8

import json

import tornado.web
import tornado.gen
import bson
import bson.errors

from .pagination import Pagination, PageNumberPagination


class MetaModelAPIHandler(type):

    def __new__(mcs, name, bases, attributes):
        cls = type.__new__(mcs, name, bases, attributes)

        if cls.model:
            cls.name = cls.model.__collection__.replace('_', '-')
            cls.path = cls.name

        return cls


class APIHandler(tornado.web.RequestHandler):

    serializers = {}
    paginator = None
    authentication = None

    def initialize(self):
        self.data = {}
        self.query = {}
        self.paginator = self.get_paginator()
        self.authentication = self.get_authentication()

    def write_error(self, status_code, details=None, **kwargs):
        data = {
            'status': 'error',
            'status_code': status_code,
            'details': details or {}
        }

        self.write(data)

    def get_method_serializers(self):
        return self.serializers.get(self.request.method, {})

    def get_query_serializer(self):
        return self.get_method_serializers().get('query')

    def get_body_serializer(self):
        return self.get_method_serializers().get('body')

    def get_paginator(self):
        return self.paginator

    def get_authentication(self):
        return self.authentication

    @tornado.gen.coroutine
    def prepare(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'application/json')

        if self.authentication:
            auth = yield self.authentication.authenticate(self.request)

            if not auth:
                return self.send_error(
                    401, details={'request_error': 'Authentication failed'}
                )

            self.request.auth = auth

        if self.request.body:
            try:
                self.data = json.loads(self.request.body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError, TypeError):
                return self.send_error(
                    400, details={'request_error': 'Unable to parse JSON'}
                )

            serializer = self.get_body_serializer()

            if serializer:
                try:
                    self.data = yield serializer(data=self.data).validate()
                except serializer.ValidationError as e:
                    return self.send_error(400, details=e.error)

            self.data.pop('_id', None)

        self.query = {}
        for key, value in self.request.query_arguments.items():
            self.query[key] = value[0].decode('utf-8')

        serializer = self.get_query_serializer()

        if serializer:
            try:
                self.query = yield serializer(data=self.query).validate()
            except serializer.ValidationError as e:
                return self.send_error(400, details=e.error)

        if self.paginator:
            self.paginator.bind(**self.query)


class ModelAPIHandler(APIHandler, metaclass=MetaModelAPIHandler):

    model = None
    lookup_field = '_id'

    @classmethod
    def get_url_spec(cls):
        url_pattern = r'/{}/?(\w*)/?'.format(cls.path)
        return tornado.web.url(url_pattern, cls, name=cls.name)

    def initialize(self):
        self.serializer = self.get_model_serializer()
        super().initialize()

    def get_queryset(self):
        return self.model.objects.filter()

    def get_paginator(self):
        queryset = self.get_queryset()

        if self.paginator and isinstance(self.paginator, Pagination):
            return self.paginator
        else:
            return PageNumberPagination(queryset, self.serializer)

    def get_body_serializer(self):
        return super().get_body_serializer() or self.model

    def get_model_serializer(self):
        return self.get_method_serializers().get('model', self.model)

    @tornado.gen.coroutine
    def get_instance(self, value):
        if self.lookup_field == '_id':
            try:
                value = bson.objectid.ObjectId(value)
            except bson.errors.InvalidId:
                return self.send_error(
                    400, details={'request_error': 'Invalid Id'}
                )

        try:
            query = {self.lookup_field: value}
            instance = yield self.model.objects.get(**query)
        except self.model.DoesNotExist:
            return self.send_error(
                404, details={'request_error': 'Object not found'}
            )

        return instance

    @tornado.gen.coroutine
    def options(self, *args, **kwargs):
        data = {
            'input': (yield self.get_body_serializer().get_metadata()),
            'output': (yield self.serializer.get_metadata()),
            'lookup_field': self.lookup_field
        }

        self.set_status(200)
        self.write(data)

    @tornado.gen.coroutine
    def get(self, key=None):
        if key:
            instance = yield self.get_instance(key)
            self.write((yield self.serializer(instance=instance).get_data()))
        else:
            self.write((yield self.paginator.paginate()))

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        try:
            instance = yield self.model.objects.create(**self.data)
        except self.model.ValidationError as e:
            return self.send_error(400, details=e.error)

        self.set_status(201)
        self.write((yield self.serializer(instance=instance).get_data()))

    @tornado.gen.coroutine
    def put(self, key):
        instance = yield self.get_instance(key)

        try:
            yield instance.update(**self.data)
        except self.model.ValidationError as e:
            return self.send_error(400, details=e.error)

        self.set_status(200)
        self.write((yield self.serializer(instance=instance).get_data()))

    @tornado.gen.coroutine
    def patch(self, key):
        yield self.put(key)

    @tornado.gen.coroutine
    def delete(self, key):
        instance = yield self.get_instance(key)

        yield instance.delete()

        self.set_status(200)
        self.write({})
