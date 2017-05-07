import unittest

from monstro.orm import db
from monstro.orm.proxy import MotorProxy


class DBTest(unittest.TestCase):

    def test_proxy(self):
        self.assertIsInstance(db.client, MotorProxy)
        self.assertIsInstance(db.database, MotorProxy)
