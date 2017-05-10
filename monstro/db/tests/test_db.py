import unittest

from monstro.db import db
from monstro.db.proxy import MotorProxy


class DBTest(unittest.TestCase):

    def test_proxy(self):
        self.assertIsInstance(db.client, MotorProxy)
        self.assertIsInstance(db.database, MotorProxy)
