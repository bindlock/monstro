# coding=utf-8

import unittest
from monstro.utils import Choices

from monstro.forms import widgets


class WidgetTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.Widget('test', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'test',
            'attrs': {'key': 'value'},
        }, widget.get_metadata())


class InputTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.Input('hidden', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'input',
            'attrs': {'key': 'value', 'type': 'hidden'},
        }, widget.get_metadata())


class TextAreaTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.TextArea(attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'textarea',
            'attrs': {'key': 'value'},
        }, widget.get_metadata())


class SelectTest(unittest.TestCase):

    def test_get_metadata(self):
        choice = Choices(
            ('A', 'a', 'A'),
            ('B', 'b', 'B')
        )
        widget = widgets.Select(
            choices=choice.choices, attributes={'key': 'value'}
        )

        self.assertEqual({
            'tag': 'select',
            'attrs': {'key': 'value'},
            'options': [
                {'label': 'A', 'value': 'a'},
                {'label': 'B', 'value': 'b'}
            ],
        }, widget.get_metadata())