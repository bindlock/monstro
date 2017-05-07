import unittest

import pymongo

from monstro import orm
from monstro.orm import proxy
import monstro.testing


class TestModel(orm.Model):

    name = orm.String()

    class Meta:
        collection = 'test'


class AutoReconnectTest(unittest.TestCase):

    def test(self):

        @proxy.autoreconnect()
        def f():
            return 1

        self.assertEqual(1, f())

    def test_error(self):

        @proxy.autoreconnect(retries=1)
        def f():
            raise pymongo.errors.AutoReconnect()

        with self.assertRaises(pymongo.errors.AutoReconnect):
            f()


class MotorProxyTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    async def test(self):
        instance = await TestModel.objects.create(name='Test')

        self.assertTrue(instance._id)

    def test_get_attribute(self):
        instance = proxy.MotorProxy(object)
        attribute = instance.__name__

        self.assertIsInstance(attribute, str)

    def test_get_item(self):
        instance = proxy.MotorProxy({'__name__': 'name'})

        self.assertIsInstance(instance['__name__'], str)

    def test_repr(self):
        self.assertEqual(
            'MotorProxy({})'.format(repr(object)),
            repr(proxy.MotorProxy(object))
        )

    def test_str(self):
        self.assertEqual(
            'MotorProxy({})'.format(str(object)), str(proxy.MotorProxy(object))
        )
