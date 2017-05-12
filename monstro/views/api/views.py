import json

import tornado.web

from monstro.forms import ModelForm
from monstro.views import views, paginators
from monstro.views.mixins import (
    ModelResponseMixin,
    ListResponseMixin,
    DetailResponseMixin
)

from . import mixins


class MetaModelAPIView(type):

    def __new__(mcs, name, bases, attributes):
        cls = type.__new__(mcs, name, bases, attributes)

        if cls.model:
            cls.name = cls.model.Meta.collection.name.replace('_', '-')
            cls.path = cls.name

        return cls


class APIView(views.View):

    form_class = None

    async def get_form_class(self):
        return self.form_class

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, details=None, **kwargs):
        self.write({
            'status': 'error',
            'code': status_code,
            'details': details or {'message': self._reason}
        })

    async def prepare(self):
        await super().prepare()

        if self.request.body:
            try:
                self.data = json.loads(self.request.body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError, TypeError):
                return self.send_error(400, reason='Unable to parse JSON')

            form_class = await self.get_form_class()

            if form_class:
                form = form_class(data=self.data)

                try:
                    await form.validate()
                except form.ValidationError as e:
                    if isinstance(e.error, str):
                        return self.send_error(400, reason=e.error)

                    return self.send_error(400, details=e.error)

                self.data = form.data
                self.data.pop('_id', None)


class ListAPIView(ListResponseMixin, APIView):

    pass


class DetailAPIView(DetailResponseMixin, APIView):

    pass


class CreateAPIView(ModelResponseMixin,
                    mixins.CreateAPIMixin,
                    APIView):

    pass


class UpdateAPIView(ModelResponseMixin,
                    mixins.UpdateAPIMixin,
                    APIView):

    pass


class DeleteAPIView(ModelResponseMixin,
                    mixins.DeleteAPIMixin,
                    APIView):

    pass


class ModelAPIView(ListResponseMixin,  # pylint:disable=R0901
                   DetailResponseMixin,
                   mixins.CreateAPIMixin,
                   mixins.UpdateAPIMixin,
                   mixins.DeleteAPIMixin,
                   APIView, metaclass=MetaModelAPIView):

    @classmethod
    def get_url(cls):
        return tornado.web.url(
            r'/{}/(?P<{}>\w*)'.format(cls.path, cls.lookup_field), cls,
            name=cls.name
        )

    async def prepare(self):
        authenticators = await self.get_authenticators()

        if authenticators:
            for authenticator in authenticators:
                self.session = await authenticator.authenticate(self)

                if self.session:
                    break
            else:
                raise tornado.web.HTTPError(401)

        await super().prepare()

    async def get_paginator(self):
        return paginators.PageNumberPaginator(await self.get_form_class())

    async def get_form_class(self):
        form_class = await super().get_form_class()

        if not form_class:
            Meta = type('Meta', (), {'model': await self.get_model()})
            form_class = type('ModelForm', (ModelForm,), {'Meta': Meta})

        return form_class

    async def get(self, *args, **kwargs):
        if self.path_kwargs.get(self.lookup_field):
            instance = await self.get_object()
            form = (await self.get_form_class())(instance=instance)

            return self.finish(await form.serialize())

        return self.finish(await self.paginate())
