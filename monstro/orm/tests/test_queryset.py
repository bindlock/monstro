# coding=utf-8

import uuid
import random

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.forms import fields

from monstro.orm import model, queryset


class QuerySetTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test
        self.queryset = queryset.QuerySet(self.model)

        self.number = random.randint(10, 20)

        for i in range(self.number):
            yield self.model.objects.create(name='test{}'.format(i))

    def test_init(self):
        self.assertEqual(self.model, self.queryset.model)

    @tornado.testing.gen_test
    def test_filter(self):
        count = yield self.queryset.filter().count()

        self.assertEqual(self.number, count)

    @tornado.testing.gen_test
    def test_first_last(self):
        first = yield self.queryset.filter().first()
        last = yield self.queryset.filter().last()

        self.assertTrue(first.name < last.name)

    @tornado.testing.gen_test
    def test_filter_with_query(self):
        count = yield self.queryset.filter(name='test0').count()

        self.assertEqual(1, count)

    @tornado.testing.gen_test
    def test_all(self):
        items = yield self.queryset.filter().all()

        self.assertEqual(self.number, len(items))

    @tornado.testing.gen_test
    def test_slice(self):
        items = yield self.queryset.filter()[1:7]

        self.assertEqual(6, len(items))

    @tornado.testing.gen_test
    def test_slice_by_items(self):
        yield self.queryset.filter().all()
        items = yield self.queryset[1:7]

        self.assertEqual(6, len(items))

    @tornado.testing.gen_test
    def test_slice_left(self):
        number = random.randint(5, 7)

        items = yield (yield self.queryset.filter()[number:]).all()

        self.assertEqual(self.number - number, len(items))

    @tornado.testing.gen_test
    def test_slice_right(self):
        number = random.randint(5, 7)

        items = yield (yield self.queryset.filter()[:number]).all()

        self.assertEqual(number, len(items))

    @tornado.testing.gen_test
    def test_slice_index(self):
        number = random.randint(5, 7)

        instance = yield self.queryset.filter()[number]

        self.assertEqual('test{}'.format(number), instance.name)

    @tornado.testing.gen_test
    def test_chain_query(self):
        instance = yield self.queryset.filter().get(name='test0')

        self.assertEqual('test0', instance.name)
