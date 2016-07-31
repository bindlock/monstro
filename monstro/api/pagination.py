# coding=utf-8

import math

import tornado.gen


DEFAULT_LIMIT = 50


class Pagination(object):

    query_keys = {}

    def __init__(self, queryset, serializer, query_keys=None):
        self.queryset = queryset
        self.serializer = serializer
        self.query_keys = query_keys or self.query_keys
        self.data = {}

    def bind(self, **kwargs):
        raise NotImplementedError()

    def get_offset(self):
        raise NotImplementedError()

    def get_limit(self):
        raise NotImplementedError()

    @tornado.gen.coroutine
    def paginate(self):
        offset = self.get_offset()
        limit = self.get_limit()
        size = limit - offset

        count = yield self.queryset.count()
        instances = yield self.queryset[offset:limit]

        self.data['page'] = self.page
        self.data['count'] = count
        self.data['pages'] = int(math.ceil(float(count) / size))

        items = []
        for instance in instances:
            if isinstance(instance, self.serializer):
                items.append((yield instance.get_data()))
                continue

            items.append((yield self.serializer(instance=instance).get_data()))

        self.data['items'] = items

        return self.data


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
        return self.limit
