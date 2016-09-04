# coding=utf-8

import monstro.testing

from monstro import orm
from monstro.orm import utils


class TestModel(orm.Model):

    __collection__ = 'test'

    name = orm.String()


class MongoDBProxyTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    @monstro.testing.gen_test
    def test(self):
        instance = yield TestModel.objects.create(name='Test')

        self.assertTrue(instance._id)

    def test_get_attribute(self):
        proxy = utils.MongoDBProxy(object)
        proxy.__name__  # pylint:disable=W0104

    def test_repr(self):
        self.assertEqual(repr(object), repr(utils.MongoDBProxy(object)))

    def test_str(self):
        self.assertEqual(str(object), str(utils.MongoDBProxy(object)))
