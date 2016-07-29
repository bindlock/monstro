# coding=utf-8


class Widget(object):

    def __init__(self, tag, is_pair=True, value=None, attributes=None):

        self.tag = tag
        self.is_pair = is_pair
        self.value = value
        self.attributes = attributes or {}

    def get_html_template(self):
        if self.is_pair:
            return '<{tag} {attributes}>{value}</{tag}>'
        else:
            return '<{tag} {attributes}>'

    def get_value(self):
        if self.value and not isinstance(self.value, str):
            return ''.join(widget.render() for widget in self.value)
        else:
            return self.value

    def render_attributes(self):
        attributes = []

        for key, value in sorted(self.attributes.items(), key=lambda x: x[0]):
            if isinstance(value, bool) and value:
                attributes.append(key)
            else:
                attributes.append('{}="{}"'.format(key, value))

        return ' '.join(attributes).strip()

    def get_render_kwargs(self):
        return {
            'tag': self.tag,
            'value': self.get_value() or '',
            'attributes': self.render_attributes()
        }

    def render(self):
        return self.get_html_template().format(**self.get_render_kwargs())

    def get_metadata(self, with_html=True):
        data = {
            'tag': self.tag, 'is_pair': self.is_pair,
            'attrs': self.attributes
        }

        data.update(
            {'html': self.render(), 'value': self.get_value()}
            if with_html else {}
        )

        return data
