# coding=utf-8

import tornado.web
import tornado.gen

import monstro.testing
from monstro.forms import String
from monstro.orm import Model

from monstro.views.pagination import (
    Pagination, PageNumberPagination, LimitOffsetPagination
)

class User(Model):

    __collection__ = 'users'

    value = String()


class PaginationTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.bind()

    def test_get_offset__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.get_offset()

    def test_get_limit__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.get_limit()

    @tornado.testing.gen_test
    def test_serialize(self):
        pagination = Pagination()

        self.assertEqual(1, (yield pagination.serialize(1)))

    @tornado.testing.gen_test
    def test_serialize__serializer(self):
        pagination = Pagination(self.TestModel)
        instance = self.TestModel(data={'value': 'test'})

        self.assertEqual(
            {'value': 'test', '_id': None},
            (yield pagination.serialize(instance))
        )

    @tornado.testing.gen_test
    def test_serialize__other_serializer(self):
        pagination = Pagination(self.TestModel)
        instance = User(data={'value': 'test'})

        self.assertEqual(
            {'value': 'test', '_id': None},
            (yield pagination.serialize(instance))
        )


class PageNumberPaginationTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.page)
        self.assertEqual(1, pagination.count)

    def test_get_offset(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(0, pagination.get_offset())

    def test_get_limit(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.get_limit())

    @tornado.testing.gen_test
    def test_paginate(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        for i in range(5):
            yield self.TestModel.objects.create(value=str(i))

        data = yield pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(1, data['pages']['current'])
        self.assertEqual(2, data['pages']['next'])
        self.assertEqual(5, data['pages']['count'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('0', data['items'][0].value)


class LimitOffsetPaginationTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(1, pagination.limit)
        self.assertEqual(2, pagination.offset)

    def test_get_offset(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(2, pagination.get_offset())

    def test_get_limit(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(3, pagination.get_limit())

    @tornado.testing.gen_test
    def test_paginate(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        for i in range(5):
            yield self.TestModel.objects.create(value=str(i))

        data = yield pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(3, data['pages']['current'])
        self.assertEqual(2, data['pages']['previous'])
        self.assertEqual(4, data['pages']['next'])
        self.assertEqual(5, data['pages']['count'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('2', data['items'][0].value)
