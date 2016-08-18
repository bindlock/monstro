# coding=utf-8

import json

import tornado.web
import tornado.gen

from monstro.views import views, mixins, pagination

from . import mixins as api_mixins


class MetaModelAPIView(type):

    def __new__(mcs, name, bases, attributes):
        cls = type.__new__(mcs, name, bases, attributes)

        if cls.model:
            cls.name = cls.model.__collection__.replace('_', '-')
            cls.path = cls.name

        return cls


class APIView(views.View):

    authentication = None
    form_class = None

    def initialize(self):
        super().initialize()
        self.data = {}
        self.query = {}
        self.form_class = self.get_form_class()

    def get_form_class(self):
        return self.form_class

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, details=None, **kwargs):
        self.write({
            'status': 'error',
            'status_code': status_code,
            'details': details or {'request_error': self._reason}
        })

    @tornado.gen.coroutine
    def prepare(self):
        yield super().prepare()

        if self.request.body:
            try:
                self.data = json.loads(self.request.body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError, TypeError):
                return self.send_error(400, reason='Unable to parse JSON')

            if self.form_class:
                form = self.form_class(data=self.data)

                try:
                    self.data = yield form.validate()
                except self.form_class.ValidationError as e:
                    return self.send_error(400, details=e.error)

            self.data.pop('_id', None)

        self.query = self.request.GET


class ListAPIView(mixins.ListResponseMixin, APIView):

    pass


class DetailAPIView(mixins.DetailResponseMixin, APIView):

    pass


class CreateAPIView(mixins.ModelResponseMixin,
                    api_mixins.CreateAPIMixin,
                    APIView):

    pass


class UpdateAPIView(mixins.ModelResponseMixin,
                    api_mixins.UpdateAPIMixin,
                    APIView):

    pass


class DeleteAPIView(mixins.ModelResponseMixin,
                    api_mixins.DeleteAPIMixin,
                    APIView):

    pass


class ModelAPIView(mixins.ListResponseMixin,
                   mixins.DetailResponseMixin,
                   api_mixins.CreateAPIMixin,
                   api_mixins.UpdateAPIMixin,
                   api_mixins.DeleteAPIMixin,
                   APIView, metaclass=MetaModelAPIView):

    @classmethod
    def get_url_spec(cls):
        url_pattern = r'/{}/?(?P<{}>\w*)/?'.format(cls.path, cls.lookup_field)
        return tornado.web.url(url_pattern, cls, name=cls.name)

    def get_pagination(self):
        return pagination.PageNumberPagination(self.form_class)

    def get_form_class(self):
        return super().get_form_class() or self.model

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        if self.path_kwargs.get(self.lookup_field):
            instance = yield self.get_object()
            form = self.form_class(instance=instance)

            return self.finish((yield form.serialize()))

        return self.finish((yield self.paginate()))
