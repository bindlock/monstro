# coding=utf-8

from .decorators import autoreconnect


class MongoDBProxy(object):

    def __init__(self, instance):
        self.instance = instance

    def __getattr__(self, attribute):
        attribute = getattr(self.instance, attribute)

        if callable(attribute):
            return autoreconnect()(attribute)

        return self.__class__(attribute)

    def __getitem__(self, item):
        return self.instance[item]

    def __repr__(self):
        return repr(self.instance)

    def __str__(self):
        return str(self.instance)
