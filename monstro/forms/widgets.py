# coding=utf-8


class Widget(object):

    def __init__(self, tag, value=None, attributes=None):
        self.tag = tag
        self.value = value
        self.attributes = attributes or {}

    def get_options(self):
        return {'tag': self.tag, 'attrs': self.attributes}


class Input(Widget):

    def __init__(self, type_, **kwargs):
        super().__init__('input', **kwargs)
        self.attributes['type'] = type_


class TextArea(Widget):

    def __init__(self, **kwargs):
        super().__init__('textarea', **kwargs)


class Select(Widget):

    def __init__(self, choices, **kwargs):
        super().__init__('select', **kwargs)
        self.choices = choices

    def get_options(self, *args, **kwargs):
        data = super().get_options(*args, **kwargs)
        data['options'] = [
            dict(zip(('value', 'label'), choice)) for choice in self.choices
        ]
        return data
