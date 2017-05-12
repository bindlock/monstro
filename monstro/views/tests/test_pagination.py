from monstro.db import Model, String
import monstro.testing

from monstro.views.paginators import (
    Paginator, PageNumberPaginator, LimitOffsetPaginator
)

class User(Model):

    value = String()

    class Meta:
        collection = 'users'


class PaginatorTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        value = String()

        class Meta:
            collection = 'test'

    def test_bind__not_implemented(self):
        pagination = Paginator()

        with self.assertRaises(NotImplementedError):
            pagination.bind()

    def test_get_offset__not_implemented(self):
        pagination = Paginator()

        with self.assertRaises(NotImplementedError):
            pagination.get_offset()

    def test_get_limit__not_implemented(self):
        pagination = Paginator()

        with self.assertRaises(NotImplementedError):
            pagination.get_limit()


class PageNumberPaginatorTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        value = String()

        class Meta:
            collection = 'test'

    def test_bind(self):
        pagination = PageNumberPaginator()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.page)
        self.assertEqual(1, pagination.count)

    def test_get_offset(self):
        pagination = PageNumberPaginator()
        pagination.bind(page=1, count=1)

        self.assertEqual(0, pagination.get_offset())

    def test_get_limit(self):
        pagination = PageNumberPaginator()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.get_limit())

    async def test_paginate(self):
        pagination = PageNumberPaginator()
        pagination.bind(page=1, count=1)

        for i in range(5):
            await self.TestModel.objects.create(value=str(i))

        data = await pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(1, data['pages']['current'])
        self.assertEqual(2, data['pages']['next'])
        self.assertEqual(5, data['pages']['total'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('0', data['items'][0].value)


class LimitOffsetPaginatorTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        value = String()

        class Meta:
            collection = 'test'

    def test_bind(self):
        pagination = LimitOffsetPaginator()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(1, pagination.limit)
        self.assertEqual(2, pagination.offset)

    def test_get_offset(self):
        pagination = LimitOffsetPaginator()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(2, pagination.get_offset())

    def test_get_limit(self):
        pagination = LimitOffsetPaginator()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(3, pagination.get_limit())

    async def test_paginate(self):
        pagination = LimitOffsetPaginator()
        pagination.bind(limit=1, offset=2)

        for i in range(5):
            await self.TestModel.objects.create(value=str(i))

        data = await pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(3, data['pages']['current'])
        self.assertEqual(2, data['pages']['previous'])
        self.assertEqual(4, data['pages']['next'])
        self.assertEqual(5, data['pages']['total'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('2', data['items'][0].value)
