# coding=utf-8

import monstro.testing

from monstro.orm import db


class GetDatabaseTest(monstro.testing.AsyncTestCase):

    def test_get_database(self):
        database = db.get_database()

        self.assertEqual(database, db.get_database())
