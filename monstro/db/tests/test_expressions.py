import unittest

from monstro.db import Or, Regex


class OrTest(unittest.TestCase):

    def test(self):
        self.assertEqual({'$or': [{'key': 'value'}]}, Or({'key': 'value'}))


class RegexTest(unittest.TestCase):

    def test(self):
        self.assertEqual({'key': {'$regex': 'value'}}, Regex({'key': 'value'}))
