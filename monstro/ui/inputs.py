# coding=utf-8

from .widget import Widget


class Input(Widget):

    def __init__(self, type_, **kwargs):
        super().__init__('input', is_pair=False, **kwargs)
        self.attributes['type'] = type_


class TextArea(Widget):

    def __init__(self, **kwargs):
        super().__init__('textarea', **kwargs)


class Select(Widget):

    def __init__(self, choices, **kwargs):
        self.choices = choices

        kwargs['value'] = []
        for value, title in self.choices:
            widget = Widget('option', value=title, attributes={'value': value})
            kwargs['value'].append(widget)

        super().__init__('select', **kwargs)

    def get_metadata(self, *args, **kwargs):
        data = super().get_metadata(*args, **kwargs)
        data['options'] = [
            dict(zip(('value', 'label'), choice)) for choice in self.choices
        ]
        return data
