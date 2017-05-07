import unittest

from monstro.utils.choices import Choices


class ChoicesTest(unittest.TestCase):

    def test(self):
        choices = Choices(('TEST', 'value', 'Description'))

        self.assertEqual(choices.TEST, 'value')

    def test__attribute_error(self):
        choices = Choices(('TEST', 'value', 'Description'))

        with self.assertRaises(AttributeError):
            self.__ = choices.NONE

    def test_contains(self):
        choices = Choices(('TEST', 'value', 'Description'))

        self.assertTrue('value' in choices)
