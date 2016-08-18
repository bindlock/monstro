# coding=utf-8

import tornado.gen

from .db import get_database


class QuerySet(object):

    def __init__(self, model):
        self.model = model
        self.cursor = get_database()[self.model.__collection__].find()
        self.items = []
        self.query = {}

    def __getattr__(self, attribute):
        return getattr(self.cursor, attribute)

    @tornado.gen.coroutine
    def construct(self, items):
        constructed = []

        for item in items:
            instance = self.model(data=item)
            yield instance.construct()
            constructed.append(instance)

        return constructed

    @tornado.gen.coroutine
    def next(self):
        if (yield self.cursor.fetch_next):
            item = self.cursor.next_object()
            instance = (yield self.construct([item]))[0]

            return instance

    def filter(self, **query):
        self.query.update(query)
        cursor = get_database()[self.model.__collection__]

        self.cursor = cursor.find(self.query)

        return self

    @tornado.gen.coroutine
    def get(self, **query):
        for key, value in query.items():
            query[key] = (
                yield self.model.__fields__[key].to_internal_value(value)
            )

        self.query.update(query)
        cursor = get_database()[self.model.__collection__]

        data = yield cursor.find_one(self.query)

        if not data:
            raise self.model.DoesNotExist()

        instance = self.model(data=data)
        yield instance.construct()

        return instance

    @tornado.gen.coroutine
    def first(self):
        self.filter().limit(1).sort('_id', 1)
        return (yield self.next())

    @tornado.gen.coroutine
    def last(self):
        self.filter().limit(1).sort('_id', -1)
        return (yield self.next())

    @tornado.gen.coroutine
    def all(self, length=None):
        if length:
            items = yield self.cursor.to_list(length)
            self.items = yield self.construct(items)
            return self.items

        while True:
            item = yield self.next()

            if item:
                self.items.append(item)
            else:
                break

        return self.items

    @tornado.gen.coroutine
    def __getitem__(self, sliced):
        if self.items:
            return self.items[sliced]

        if isinstance(sliced, slice):
            if sliced.start is not None and sliced.stop is not None:
                self.cursor.skip(sliced.start)
                instances = yield self.all(sliced.stop - sliced.start)
                return instances
            elif sliced.start is not None:
                self.cursor.skip(sliced.start)
            elif sliced.stop is not None:
                self.cursor.limit(sliced.stop)
        else:
            data = yield self.all()
            return data[sliced]

        return self
