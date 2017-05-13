import uuid
import random

import monstro.testing
from monstro.db import Raw, fields
from monstro.db import model, exceptions
from monstro.db.queryset import QuerySet
from monstro.db.proxy import MotorProxy


class QuerySetTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Related(model.Model):

            name = fields.String()

            class Meta:
                collection = uuid.uuid4().hex

        class Test(model.Model):

            key = fields.ForeignKey(to=Related, to_field='name')
            name = fields.String()
            age = fields.Integer(required=False)

            class Meta:
                collection = uuid.uuid4().hex

        self.related_model = Related
        self.model = Test

        self.number = random.randint(10, 20)

        self.related = await Related.objects.create(name='test')

        for i in range(self.number):
            await self.model.objects.create(
                name='test{}'.format(i), age=0, key=self.related
            )

    async def test_validate__invalid_field(self):
        queryset = self.model.objects.filter(test='1')

        with self.assertRaises(exceptions.InvalidQuery):
            await queryset.validate()

    async def test_validate__validation_error(self):
        queryset = self.model.objects.filter(key=None)
        await queryset.validate()

        self.assertEqual({'key': None}, queryset.query)

    async def test_validate__raw_query(self):
        query = {'name': 'test'}
        queryset = self.model.objects.raw(query)
        await queryset.validate()

        self.assertEqual(query, queryset.query)

    async def test_validate__raw_subquery(self):
        queryset = self.model.objects.filter(name__lte='', name__gte='')
        await queryset.validate()

        self.assertEqual(
            {'name': {'$gte': '', '$lte': ''}},
            queryset.query
        )

    async def test_cursor_method(self):
        queryset = self.model.objects.filter()

        self.assertEqual(self.number, len(await queryset.distinct('name')))

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

        instance = await self.model.objects.filter()[number]

        self.assertEqual('test{}'.format(number), instance.name)

    async def test_chain_query(self):
        instance = await self.model.objects.filter().get(name='test0')

        self.assertEqual('test0', instance.name)

    def test_proxy(self):
        queryset = self.model.objects.filter()

        self.assertIsInstance(queryset.collection, MotorProxy)
        self.assertIsInstance(queryset.cursor, MotorProxy)

    async def test_iterable(self):
        queryset = self.model.objects.filter(key__in=['test', 't'])
        items = []

        async for item in queryset:
            items.append(item)

        self.assertEqual(self.number, await queryset.count())
        self.assertEqual(self.number, len(items))

    async def test_only(self):
        queryset = self.model.objects.only('name')

        async for item in queryset:
            self.assertEqual(None, item.age)

    async def test_values(self):
        queryset = self.model.objects.values()

        async for item in queryset:
            self.assertIsInstance(item, dict)
            self.assertIn('_id', item)
            self.assertIn('name', item)
            self.assertIn('age', item)

    async def test_suffix_query(self):
        choices = ['test', 't']
        queryset = self.model.objects.filter(key__in=choices)
        await queryset.validate()

        self.assertEqual({'key': {'$in': choices}}, queryset.query)

    async def test_raw_subquery(self):
        subquery = Raw({'$in': ['test']})
        queryset = self.model.objects.filter(key=subquery)
        await queryset.validate()

        self.assertEqual({'key': subquery.query}, queryset.query)

    async def test_raw_fields(self):
        queryset = self.model.objects.raw_fields('key')

        async for item in queryset:
            self.assertIsInstance(item.key, str)
