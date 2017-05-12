import unittest

from monstro.conf import settings
from monstro.db import databases
from monstro.db.proxy import MotorProxy


class RouterTest(unittest.TestCase):

    def test_databases(self):
        database = databases.get()

        self.assertIsInstance(database, MotorProxy)
        self.assertEqual(
            'test_{}'.format(settings.databases[0]['name']),
            database.name
        )

    def test_set(self):
        database = databases.get()

        databases.set('another', database.instance)

        self.assertEqual(database.name, databases.get('another').name)
