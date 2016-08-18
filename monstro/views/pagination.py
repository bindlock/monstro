# coding=utf-8

import math

import tornado.gen


DEFAULT_LIMIT = 50


class Pagination(object):

    query_keys = {}

    def __init__(self, serializer=None, query_keys=None):
        self.serializer = serializer
        self.query_keys = query_keys or self.query_keys

    def bind(self, **kwargs):
        raise NotImplementedError()

    def get_offset(self):
        raise NotImplementedError()

    def get_limit(self):
        raise NotImplementedError()

    @tornado.gen.coroutine
    def serialize(self, instance):
        if self.serializer:
            if isinstance(instance, self.serializer):
                return (yield instance.serialize())

            return (yield self.serializer(instance=instance).serialize())

        return instance

    @tornado.gen.coroutine
    def paginate(self, queryset):
        offset = self.get_offset()
        limit = self.get_limit()
        size = limit - offset

        count = yield queryset.count()
        instances = yield queryset[offset:limit]

        pages = {}
        pages['current'] = int(math.ceil(float(offset) / size)) + 1
        pages['count'] = int(math.ceil(float(count) / size))

        if pages['current'] > 1:
            pages['previous'] = pages['current'] - 1

        if pages['current'] < pages['count']:
            pages['next'] = pages['current'] + 1

        items = []

        for instance in instances:
            items.append((yield self.serialize(instance)))

        return {'pages': pages, 'items': items}


class PageNumberPagination(Pagination):

    query_keys = {
        'page': 'page',
        'count': 'count'
    }

    def bind(self, **kwargs):
        self.page = int(kwargs.get(self.query_keys['page'], 1))
        self.count = int(kwargs.get(self.query_keys['count'], DEFAULT_LIMIT))

    def get_offset(self):
        return (self.page - 1) * self.count

    def get_limit(self):
        return self.page * self.count


class LimitOffsetPagination(Pagination):

    query_keys = {
        'limit': 'limit',
        'offset': 'offset'
    }

    def bind(self, **kwargs):
        self.limit = int(kwargs.get(self.query_keys['limit'], DEFAULT_LIMIT))
        self.offset = int(kwargs.get(self.query_keys['offset'], 0))

    def get_offset(self):
        return self.offset

    def get_limit(self):
        return self.offset + self.limit
