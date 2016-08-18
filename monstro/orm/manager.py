# coding=utf-8

import tornado.gen

from .queryset import QuerySet


class Manager(object):

    def bind(self, **kwargs):
        self.__dict__.update(**kwargs)

    def __getattr__(self, attribute):
        return getattr(QuerySet(self.model), attribute)

    @tornado.gen.coroutine
    def create(self, **kwargs):
        instance = yield self.model(data=kwargs).save()
        return instance
