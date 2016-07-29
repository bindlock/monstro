# coding=utf-8

import unittest

from .choice import Choice


class ChoiceTest(unittest.TestCase):

    def test(self):
        choices = Choice(('TEST', 'value', 'Description'))

        self.assertEqual(choices.TEST, 'value')

    def test__attribute_error(self):
        choices = Choice(('TEST', 'value', 'Description'))

        with self.assertRaises(AttributeError):
            self.__ = choices.NONE

    def test_contains(self):
        choices = Choice(('TEST', 'value', 'Description'))

        self.assertTrue('value' in choices)
