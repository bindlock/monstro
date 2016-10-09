# coding=utf-8

import copy
import logging

import pymongo

from . import db, exceptions


logger = logging.getLogger('monstro')


class QuerySet(object):

    def __init__(self, model, query=None, offset=0, limit=0,
                 sorts=None, collection=None):
        self.model = model
        self.query = query or {}
        self.offset = offset
        self.limit = limit

        self._sorts = sorts or []
        self._collection = collection

        self._cursor = None
        self._validated = False

    def __getattr__(self, attribute):
        return getattr(self.clone().cursor, attribute)

    @property
    def cursor(self):
        if not self._cursor:
            self._cursor = self.collection.find(
                self.query, skip=self.offset, limit=self.limit, sort=self.sorts
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

    def __aiter__(self):
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
        kwargs.setdefault('sorts', copy.copy(self._sorts))
        kwargs.setdefault('collection', self._collection)
        return QuerySet(**kwargs)

    async def validate_query(self):
        for key, value in self.query.items():
            if isinstance(value, dict):
                if all(k.startswith('$') for k in value):
                    continue

            try:
                field = self.model.__fields__[key]
                value = await field.to_python(copy.deepcopy(value))

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
        return self.clone(sorts=self.sorts + list(fields))

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
