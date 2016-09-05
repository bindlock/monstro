# coding=utf-8

import tornado.gen

from .db import get_database


class QuerySet(object):

    def __init__(self, model):
        self.model = model
        self.cursor = None
        self.items = []
        self.query = {}

    def __getattr__(self, attribute):
        if self.cursor is None:
            collection = get_database()[self.model.__collection__]
            self.cursor = collection.find(self.query)

        return getattr(self.cursor, attribute)

    @tornado.gen.coroutine
    def to_python(self, items):
        constructed = []

        for item in items:
            instance = yield self.model(data=item).to_python()
            constructed.append(instance)

        return constructed

    @tornado.gen.coroutine
    def next(self):
        if (yield self.fetch_next):
            item = self.next_object()
            instance = (yield self.to_python([item]))[0]

            return instance

    def filter(self, **query):
        self.query.update(query)
        return self

    @tornado.gen.coroutine
    def get(self, **query):
        for key, value in query.items():
            if key == '_id':
                continue

            try:
                field = self.model.__fields__[key]
                value = yield field.to_python(value)
                value = yield field.to_internal_value(value)
            except (KeyError, self.model.ValidationError):
                pass

            query[key] = value

        self.query.update(query)
        cursor = get_database()[self.model.__collection__]

        data = yield cursor.find_one(self.query)

        if not data:
            raise self.model.DoesNotExist()

        instance = yield self.model(data=data).to_python()

        return instance

    @tornado.gen.coroutine
    def first(self):
        self.limit(1).sort('_id', 1)
        return (yield self.next())

    @tornado.gen.coroutine
    def last(self):
        self.limit(1).sort('_id', -1)
        return (yield self.next())

    @tornado.gen.coroutine
    def all(self, length=None):
        if length:
            items = yield self.to_list(length)
            self.items = yield self.to_python(items)
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
                self.skip(sliced.start)
                instances = yield self.all(sliced.stop - sliced.start)
                return instances
            elif sliced.start is not None:
                self.skip(sliced.start)
            elif sliced.stop is not None:
                self.limit(sliced.stop)
        else:
            data = yield self.all()
            return data[sliced]

        return self
