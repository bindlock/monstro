import copy

import pymongo

from . import db, exceptions


class QuerySet(object):

    def __init__(self, model, query=None, offset=0, limit=0,
                 fields=None, sorts=None, collection=None, raw=False,
                 raw_fields=None):

        self.model = model
        self.query = query or {}
        self.offset = offset
        self.limit = limit

        self.fields = fields
        self._sorts = sorts or []
        self._collection = collection

        self.raw = raw
        self._raw_fields = raw_fields or []
        self._cursor = None

    def __getattr__(self, attribute):
        return getattr(self.clone().cursor, attribute)

    @property
    def cursor(self):
        if not self._cursor:
            self._cursor = self.collection.find(
                self.query, self.fields or None, skip=self.offset,
                limit=self.limit, sort=self.sorts
            )

        return self._cursor

    @property
    def sorts(self):
        sorts = []

        for sort in self._sorts:
            if sort.lstrip('-') not in self.model.Meta.fields:
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
        return db.database[self.model.Meta.collection]

    async def __aiter__(self):
        clone = self.clone()
        await clone.validate()
        return clone

    async def __anext__(self):
        if await self.cursor.fetch_next:
            data = self.cursor.next_object()

            if self.raw:
                return data

            return await self.model(**data).deserialize()

        raise StopAsyncIteration()

    def clone(self, **kwargs):
        kwargs.setdefault('model', self.model)
        kwargs.setdefault('query', copy.copy(self.query))
        kwargs.setdefault('offset', self.offset)
        kwargs.setdefault('limit', self.limit)
        kwargs.setdefault('fields', copy.copy(self.fields))
        kwargs.setdefault('sorts', copy.copy(self._sorts))
        kwargs.setdefault('raw', self.raw)
        kwargs.setdefault('collection', self._collection)
        kwargs.setdefault('raw_fields', self._raw_fields)
        return QuerySet(**kwargs)

    async def validate(self):
        query = {}

        for key, value in self.query.items():
            if '__' in key:
                key, suffix = key.split('__')
                value = {'${}'.format(suffix): value}
            elif not (key.startswith('$') or key == '_id'):
                try:
                    value = await self.model.Meta.fields[key].serialize(value)
                except KeyError:
                    raise exceptions.InvalidQuery(
                        '{} has not field {}'.format(self.model, key)
                    )
                except:  # pylint: disable=W0702
                    pass

            if isinstance(query.get(key), dict):
                query[key].update(value)
            else:
                query[key] = value

        self.query = query

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

    def raw_fields(self, *fields):
        return self.clone(raw_fields=self._raw_fields + list(fields))

    async def count(self):
        clone = self.clone()
        await clone.validate()
        return await clone.cursor.count(True)

    async def get(self, **query):
        clone = self.filter(**query)
        clone.limit = 1

        async for item in clone:
            return item

        raise clone.model.DoesNotExist()

    async def first(self):
        clone = self.clone()
        clone._sorts.append('_id')
        return await clone.get()

    async def last(self):
        clone = self.clone()
        clone._sorts.append('-_id')
        return await clone.get()

    def all(self):
        return self.filter()

    def __getitem__(self, item):
        clone = self.clone()

        if isinstance(item, slice):
            if item.start is not None and item.stop is not None:
                clone.offset = item.start
                clone.limit = item.stop - item.start
            elif item.start is not None:
                clone.offset = item.start
            elif item.stop is not None:
                clone.limit = item.stop
        else:
            clone.offset = item
            clone.limit = 1
            return clone.get()

        return clone
