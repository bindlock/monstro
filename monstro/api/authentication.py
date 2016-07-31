# coding=utf-8

import tornado.gen


class Authentication(object):

    def authenticate(self, request):
        raise NotImplementedError()


class TokenAuthentication(Authentication):

    def __init__(self, model, lookup_field, header_name='Authorization'):
        self.model = model
        self.lookup_field = lookup_field
        self.header_name = header_name

    @tornado.gen.coroutine
    def authenticate(self, request):
        token = request.headers.get(self.header_name, '').strip()
        get_kwargs = {self.lookup_field: token}

        try:
            instance = yield self.model.objects.get(**get_kwargs)
        except self.model.DoesNotExist:
            instance = None

        return instance
