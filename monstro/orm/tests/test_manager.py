# coding=utf-8

import uuid
import random

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.forms import fields

from monstro.orm import model


class ManagerTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test

        self.number = random.randint(11, 20)

        for i in range(self.number):
            yield self.model.objects.create(name='test{}'.format(i))

    @tornado.testing.gen_test
    def test_filter(self):
        count = yield self.model.objects.filter().count()

        self.assertEqual(self.number, count)

    @tornado.testing.gen_test
    def test_filter_with_query(self):
        count = yield self.model.objects.filter(name='test10').count()

        self.assertEqual(1, count)

    @tornado.testing.gen_test
    def test_create(self):
        instance = yield self.model.objects.create(name='New')
        count = yield self.model.objects.filter(name=instance.name).count()

        self.assertEqual(1, count)
