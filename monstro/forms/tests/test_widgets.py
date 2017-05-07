import unittest

from monstro.forms import widgets
from monstro.utils import Choices


class WidgetTest(unittest.TestCase):

    def test_get_options(self):
        widget = widgets.Widget('test', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'test',
            'attrs': {'key': 'value'},
        }, widget.get_options())


class InputTest(unittest.TestCase):

    def test_get_options(self):
        widget = widgets.Input('hidden', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'input',
            'attrs': {'key': 'value', 'type': 'hidden'},
        }, widget.get_options())


class TextAreaTest(unittest.TestCase):

    def test_get_options(self):
        widget = widgets.TextArea(attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'textarea',
            'attrs': {'key': 'value'},
        }, widget.get_options())


class SelectTest(unittest.TestCase):

    def test_get_options(self):
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
        }, widget.get_options())
