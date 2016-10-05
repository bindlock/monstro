# coding=utf-8

import uuid
import random

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.forms import fields

from monstro.orm import model, exceptions
from monstro.orm.queryset import QuerySet


class QuerySetTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()
            age = fields.Integer(required=False)

        self.model = Test

        self.number = random.randint(10, 20)

        for i in range(self.number):
            yield self.model.objects.create(name='test{}'.format(i))

    @tornado.testing.gen_test
    def test_validate_query(self):
        queryset = self.model.objects.filter(age='1')

        self.assertEqual({'age': 1}, (yield queryset.validate_query()))

    @tornado.testing.gen_test
    def test_validate_query__invalid_field(self):
        queryset = self.model.objects.filter(test='1')

        with self.assertRaises(exceptions.InvalidQuery):
            yield queryset.validate_query()

    @tornado.testing.gen_test
    def test_validate_query__invalid_query(self):
        queryset = self.model.objects.filter(age='wrong')

        with self.assertRaises(exceptions.InvalidQuery):
            yield queryset.validate_query()

    @tornado.testing.gen_test
    def test_sorts(self):
        queryset = self.model.objects.filter()

        self.assertEqual([('name', -1)], queryset.order_by('-name').sorts)

    @tornado.testing.gen_test
    def test_sorts__invalid_field(self):
        queryset = self.model.objects.filter()

        with self.assertRaises(exceptions.InvalidQuery):
            __ = queryset.order_by('-wrong').sorts

    @tornado.testing.gen_test
    def test_filter(self):
        count = yield self.model.objects.filter().count()

        self.assertEqual(self.number, count)

    @tornado.testing.gen_test
    def test_first_last(self):
        first = yield self.model.objects.filter().first()
        last = yield self.model.objects.filter().last()

        self.assertTrue(first.name < last.name)

    @tornado.testing.gen_test
    def test_filter_with_query(self):
        count = yield self.model.objects.filter(name='test0').count()

        self.assertEqual(1, count)

    @tornado.testing.gen_test
    def test_all(self):
        self.assertIsInstance(self.model.objects.all(), QuerySet)

    @tornado.testing.gen_test
    def test_slice(self):
        items = self.model.objects.filter()[2:7]

        self.assertEqual(5, (yield items.count()))

    @tornado.testing.gen_test
    def test_slice_left(self):
        number = random.randint(5, 7)

        items = self.model.objects.filter()[number:]

        self.assertEqual(self.number - number, (yield items.count()))

    @tornado.testing.gen_test
    def test_slice_right(self):
        number = random.randint(5, 7)

        items = self.model.objects.filter()[:number]

        self.assertEqual(number, (yield items.count()))

    @tornado.testing.gen_test
    def test_slice_index(self):
        number = random.randint(5, 7)

        instance = yield self.model.objects.filter()[number].get()

        self.assertEqual('test{}'.format(number), instance.name)

    @tornado.testing.gen_test
    def test_chain_query(self):
        instance = yield self.model.objects.filter().get(name='test0')

        self.assertEqual('test0', instance.name)
