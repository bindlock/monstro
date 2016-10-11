# coding=utf-8

import copy
import logging

import pymongo

from . import db, exceptions


logger = logging.getLogger('monstro')


class QuerySet(object):

    def __init__(self, model, query=None, offset=0, limit=0,
                 fields=None, sorts=None, collection=None, raw=False):
        self.model = model
        self.query = query or {}
        self.offset = offset
        self.limit = limit

        self.fields = fields
        self._sorts = sorts or []
        self._collection = collection

        self.raw = raw
        self._cursor = None
        self._validated = False

    def __getattr__(self, attribute):
        return getattr(self.clone().cursor, attribute)

    @property
    def cursor(self):
        if not self._cursor:
            self._cursor = self.collection.find(
                self.query, skip=self.offset, limit=self.limit,
                fields=self.fields or None, sort=self.sorts
            )

        return self._cursor

    @property
    def sorts(self):
        sorts = []

        for sort in self._sorts:
            if sort.lstrip('-') not in self.model.__fields__:
                raise exceptions.InvalidQuery(
                    '{} has not field {}'.format(self.model, sort)
                )

            if sort.startswith('-'):
                sorts.append((sort.lstrip('-'), pymongo.DESCENDING))
            else:
                sorts.append((sort, pymongo.ASCENDING))

        return sorts

    @property
    def collection(self):
        if not self._collection:
            self._collection = db.database[self.model.__collection__]

        return self._collection

    async def __aiter__(self):
        if self.raw:
            return await self.clone().cursor.__aiter__()

        return self.clone()

    async def __anext__(self):
        if not self._validated:
            await self.validate_query()

        if await self.cursor.fetch_next:
            return await self.model(data=self.cursor.next_object()).to_python()

        raise StopAsyncIteration()

    def clone(self, **kwargs):
        kwargs.setdefault('model', self.model)
        kwargs.setdefault('query', copy.deepcopy(self.query))
        kwargs.setdefault('offset', self.offset)
        kwargs.setdefault('limit', self.limit)
        kwargs.setdefault('fields', copy.copy(self.fields))
        kwargs.setdefault('sorts', copy.copy(self._sorts))
        kwargs.setdefault('raw', copy.copy(self.raw))
        kwargs.setdefault('collection', self._collection)
        return QuerySet(**kwargs)

    async def validate_query(self):
        for key, value in self.query.items():
            if isinstance(value, dict):
                if any(key.startswith('$') for key in value):
                    continue

            try:
                field = self.model.__fields__[key]
                value = await field.to_python(value)

                if key != '_id':
                    value = await field.to_internal_value(value)
            except self.model.ValidationError as e:
                logger.warning('Invalid query: {}'.format(e))
            except KeyError:
                raise exceptions.InvalidQuery(
                    '{} has not field {}'.format(self.model, key)
                )

            self.query[key] = value

        self._validated = True

        return self.query

    def filter(self, **query):
        _query = self.query.copy()
        _query.update(query)
        return self.clone(query=_query)

    def order_by(self, *fields):
        return self.clone(sorts=self._sorts + list(fields))

    def only(self, *fields):
        return self.clone(fields=(self.fields or []) + list(fields))

    def values(self, *fields):
        queryset = self.only(*fields)
        queryset.raw = True
        return queryset

    async def count(self):
        return await self.clone().cursor.count(True)

    async def get(self, **query):
        self = self.filter(**query)
        await self.validate_query()
        self.limit = 1

        async for item in self:
            return item

        raise self.model.DoesNotExist()

    async def first(self):
        self = self.clone()
        self._sorts.append('_id')
        return await self.get()

    async def last(self):
        self = self.clone()
        self._sorts.append('-_id')
        return await self.get()

    def all(self):
        return self.filter()

    def __getitem__(self, item):
        self = self.clone()

        if isinstance(item, slice):
            if item.start is not None and item.stop is not None:
                self.offset = item.start
                self.limit = item.stop - item.start
            elif item.start is not None:
                self.offset = item.start
            elif item.stop is not None:
                self.limit = item.stop
        else:
            self.offset = item
            self.limit = 1

        return self
