# coding=utf-8

import uuid
import random

import monstro.testing
from monstro.forms import fields

from monstro.orm import model, exceptions
from monstro.orm.queryset import QuerySet
from monstro.orm.proxy import MotorProxy


class QuerySetTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()
            age = fields.Integer(required=False)

        self.model = Test

        self.number = random.randint(10, 20)

        for i in range(self.number):
            await self.model.objects.create(name='test{}'.format(i))

    async def test_validate_query(self):
        queryset = self.model.objects.filter(age='1')

        self.assertEqual({'age': 1}, await queryset.validate_query())

    async def test_validate_query__invalid_field(self):
        queryset = self.model.objects.filter(test='1')

        with self.assertRaises(exceptions.InvalidQuery):
            await queryset.validate_query()

    async def test_validate_query__invalid_query(self):
        queryset = self.model.objects.filter(age='wrong')

        with self.assertRaises(exceptions.InvalidQuery):
            await queryset.validate_query()

    def test_sorts(self):
        queryset = self.model.objects.filter()

        self.assertEqual([('name', -1)], queryset.order_by('-name').sorts)

    def test_sorts__invalid_field(self):
        queryset = self.model.objects.filter()

        with self.assertRaises(exceptions.InvalidQuery):
            __ = queryset.order_by('-wrong').sorts

    async def test_filter(self):
        count = await self.model.objects.filter().count()

        self.assertEqual(self.number, count)

    async def test_first_last(self):
        first = await self.model.objects.filter().first()
        last = await self.model.objects.filter().last()

        self.assertTrue(first.name < last.name)

    async def test_filter_with_query(self):
        count = await self.model.objects.filter(name='test0').count()

        self.assertEqual(1, count)

    def test_all(self):
        self.assertIsInstance(self.model.objects.all(), QuerySet)

    async def test_slice(self):
        items = self.model.objects.filter()[2:7]

        self.assertEqual(5, await items.count())

    async def test_slice_left(self):
        number = random.randint(5, 7)

        items = self.model.objects.filter()[number:]

        self.assertEqual(self.number - number, await items.count())

    async def test_slice_right(self):
        number = random.randint(5, 7)

        items = self.model.objects.filter()[:number]

        self.assertEqual(number, await items.count())

    async def test_slice_index(self):
        number = random.randint(5, 7)

        instance = await self.model.objects.filter()[number].get()

        self.assertEqual('test{}'.format(number), instance.name)

    async def test_chain_query(self):
        instance = await self.model.objects.filter().get(name='test0')

        self.assertEqual('test0', instance.name)

    def test_proxy(self):
        queryset = self.model.objects.filter()

        self.assertIsInstance(queryset.collection, MotorProxy)
        self.assertIsInstance(queryset.cursor, MotorProxy)

    async def test_iterable(self):
        queryset = self.model.objects.filter()
        items = []

        async for item in queryset:
            items.append(item)

        self.assertEqual(await queryset.count(), len(items))
