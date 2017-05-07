import math


DEFAULT_LIMIT = 50


class Paginator(object):

    query_keys = {}

    def __init__(self, form=None, query_keys=None):
        self.form = form
        self.query_keys = query_keys or self.query_keys

    def bind(self, **kwargs):
        raise NotImplementedError()

    def get_offset(self):
        raise NotImplementedError()

    def get_limit(self):
        raise NotImplementedError()

    async def paginate(self, queryset):
        offset = self.get_offset()
        limit = self.get_limit()
        size = limit - offset

        number = await queryset.count()

        pages = {}
        pages['current'] = int(math.ceil(float(offset) / size)) + 1
        pages['total'] = int(math.ceil(float(number) / size))

        if pages['current'] > 1:
            pages['previous'] = pages['current'] - 1

        if pages['current'] < pages['total']:
            pages['next'] = pages['current'] + 1

        items = []

        async for instance in queryset[offset:limit]:
            if self.form:
                instance = await self.form(instance=instance).serialize()

            items.append(instance)

        return {'pages': pages, 'items': items}


class PageNumberPaginator(Paginator):

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


class LimitOffsetPaginator(Paginator):

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
