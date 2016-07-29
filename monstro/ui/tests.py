# coding=utf-8

import unittest

from monstro.utils import Choice

from . import inputs
from .widget import Widget


class WidgetTest(unittest.TestCase):

    def test_render__not_pair(self):
        widget = Widget(
            'test', is_pair=False, attributes={'key': 'value', 'bool': True}
        )

        self.assertEqual('<test bool key="value">', widget.render())

    def test_render__pair(self):
        widget = Widget('test', value='a', attributes={'key': 'value'})

        self.assertEqual('<test key="value">a</test>', widget.render())

    def test_get_metadata(self):
        widget = Widget('test', value='a', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'test',
            'value': 'a',
            'is_pair': True,
            'attrs': {'key': 'value'},
            'html': '<test key="value">a</test>'
        }, widget.get_metadata())


class InputTest(unittest.TestCase):

    def test_render(self):
        widget = inputs.Input('hidden', attributes={'key': 'value'})

        self.assertEqual('<input key="value" type="hidden">', widget.render())

    def test_get_metadata(self):
        widget = inputs.Input('hidden', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'input',
            'value': None,
            'is_pair': False,
            'attrs': {'key': 'value', 'type': 'hidden'},
            'html': '<input key="value" type="hidden">'
        }, widget.get_metadata())


class TextAreaTest(unittest.TestCase):

    def test_render(self):
        widget = inputs.TextArea(value='test', attributes={'key': 'value'})

        self.assertEqual(
            '<textarea key="value">test</textarea>', widget.render()
        )

    def test_get_metadata(self):
        widget = inputs.TextArea(value='test', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'textarea',
            'value': 'test',
            'is_pair': True,
            'attrs': {'key': 'value'},
            'html': '<textarea key="value">test</textarea>',
        }, widget.get_metadata())


class SelectTest(unittest.TestCase):

    def test_render(self):
        choice = Choice(
            ('A', 'a', 'A'),
            ('B', 'b', 'B')
        )
        widget = inputs.Select(
            choices=choice.choices, attributes={'key': 'value'}
        )

        self.assertEqual(
            (
                '<select key="value">'
                '<option value="a">A</option>'
                '<option value="b">B</option>'
                '</select>'
            ), widget.render()
        )

    def test_get_metadata(self):
        choice = Choice(
            ('A', 'a', 'A'),
            ('B', 'b', 'B')
        )
        widget = inputs.Select(
            choices=choice.choices, attributes={'key': 'value'}
        )

        self.assertEqual({
            'tag': 'select',
            'is_pair': True,
            'attrs': {'key': 'value'},
            'options': [
                {'label': 'A', 'value': 'a'},
                {'label': 'B', 'value': 'b'}
            ],
            'html': (
                '<select key="value">'
                '<option value="a">A</option>'
                '<option value="b">B</option>'
                '</select>'
            ),
            'value': '<option value="a">A</option><option value="b">B</option>'
        }, widget.get_metadata())
