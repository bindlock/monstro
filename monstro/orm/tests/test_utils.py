# coding=utf-8

import monstro.testing

from monstro import orm
from monstro.orm import utils


class TestModel(orm.Model):

    __collection__ = 'test'

    name = orm.String()


class MotorProxyTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    @monstro.testing.gen_test
    def test(self):
        instance = yield TestModel.objects.create(name='Test')

        self.assertTrue(instance._id)

    def test_get_attribute(self):
        proxy = utils.MotorProxy(object)
        attribute = proxy.__name__

        self.assertIsInstance(attribute, utils.MotorProxy)

    def test_get_item(self):
        proxy = utils.MotorProxy({'__name__': 'name'})
        item = proxy['__name__']

        self.assertIsInstance(item, utils.MotorProxy)

    def test_repr(self):
        self.assertEqual(repr(object), repr(utils.MotorProxy(object)))

    def test_str(self):
        self.assertEqual(str(object), str(utils.MotorProxy(object)))
