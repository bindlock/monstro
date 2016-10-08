# coding=utf-8

import uuid
import random

import monstro.testing
from monstro.forms import fields

from monstro.orm import model


class ManagerTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test

        self.number = random.randint(11, 20)

        for i in range(self.number):
            await self.model.objects.create(name='test{}'.format(i))

    async def test_filter(self):
        count = await self.model.objects.filter().count()

        self.assertEqual(self.number, count)

    async def test_filter_with_query(self):
        count = await self.model.objects.filter(name='test10').count()

        self.assertEqual(1, count)

    async def test_create(self):
        instance = await self.model.objects.create(name='New')
        count = await self.model.objects.filter(name=instance.name).count()

        self.assertEqual(1, count)
