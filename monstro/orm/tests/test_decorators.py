# coding=utf-8

import unittest

import pymongo

from monstro.orm import decorators


class AutoReconnectTest(unittest.TestCase):

    def test(self):

        @decorators.autoreconnect()
        def f():
            return 1

        self.assertEqual(1, f())

    def test_error(self):

        @decorators.autoreconnect(retries=1)
        def f():
            raise pymongo.errors.AutoReconnect()

        with self.assertRaises(pymongo.errors.AutoReconnect):
            f()
