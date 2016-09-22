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
        instance = self.model(data=kwargs)
        yield instance.save()
        return (yield instance.to_python())
