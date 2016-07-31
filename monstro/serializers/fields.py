# coding=utf-8

import re
import json
import urllib.parse

import tornado.gen

from monstro.ui import inputs

from .exceptions import ValidationError


class Field(object):

    widget = None
    default_error_messages = {
        'required': 'Value is required',
        'invalid': 'Value is invalid',
        'unique': 'Value must be unique',
        'read_only': 'Read-only value'
    }

    def __init__(self, *, name=None, required=True, default=None, label=None,
                 unique=False, help_text=None, read_only=False,
                 validators=None, error_messages=None, widget=None):

        """Initialization instance.

        :param required (optional): value is required flag.
        :type required: bool.
        :param default (optional): default value.
        :type default: type.
        :param validators (optional): additional validators.
        :type validators: iterable of callable.
        :param error_messages (optional): custom error messages.
        :type error_messages: dict.
        """
        self.name = name
        self.required = required
        self.default = default
        self.label = label
        self.unique = unique
        self.help_text = help_text
        self.read_only = read_only
        self.validators = validators or []
        self.widget = widget or self.widget

        messages = {}

        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))

        messages.update(error_messages or {})

        self.error_messages = messages

    def bind(self, **kwargs):
        self.__dict__.update(kwargs)

    @tornado.gen.coroutine
    def validate(self, value=None, model=None):
        if value is None:
            value = self.default

        if value is None:
            if self.required:
                self.fail('required')
            else:
                return None

        yield self.is_valid(value)

        for validator in self.validators:
            yield validator(value)

        if self.unique and hasattr(self, 'model'):
            try:
                instance = yield self.model.objects.get(**{self.name: value})
            except self.model.DoesNotExist:
                instance = None

            if instance and model and instance._id != model._id:
                self.fail('unique')

        return (yield self.to_internal_value(value))

    def fail(self, error_code, **kwargs):
        raise ValidationError(
            self.error_messages[error_code].format(self, **kwargs),
            self.name
        )

    @tornado.gen.coroutine
    def is_valid(self, value):
        raise NotImplementedError()

    @tornado.gen.coroutine
    def to_representation(self, value):
        return value

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        return value

    @tornado.gen.coroutine
    def get_metadata(self):
        raise tornado.gen.Return({
            'name': self.name,
            'label': self.label or (self.name and self.name.title()),
            'help_text': self.help_text,
            'required': self.required,
            'read_only': self.read_only,
            'default': self.default and (
                yield self.to_internal_value(self.default)
            ),
            'widget': self.widget and self.widget.get_metadata(with_html=False)
        })


class TypedField(Field):

    type = type
    widget = inputs.Input('text')
    default_error_messages = {
        'invalid': 'Value must be a valid {0.type.__name__}'
    }

    @tornado.gen.coroutine
    def is_valid(self, value):
        if not isinstance(value, self.type):
            self.fail('invalid')


class BooleanField(TypedField):

    type = bool
    widget = inputs.Input('checkbox')
    default_error_messages = {
        'invalid': 'Value must be a valid boolean'
    }


class StringField(TypedField):

    type = str
    default_error_messages = {
        'invalid': 'Value must be a valid string',
        'min_length': 'String must be greater {0.min_length} characters',
        'max_length': 'String must be less {0.max_length} characters'
    }

    def __init__(self, *, min_length=None, max_length=None, **kwargs):
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def is_valid(self, value):
        yield super().is_valid(value)

        if self.min_length is not None and len(value) < self.min_length:
            self.fail('min_length')

        if self.max_length is not None and len(value) > self.max_length:
            self.fail('max_length')

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        if value is not None:
            return str(value)

        return value


class NumericField(TypedField):

    default_error_messages = {
        'invalid': 'Value must be a valid integer or float',
        'min_value': 'Number must be greater {0.min_value} characters',
        'max_value': 'Number must be less {0.max_value} characters'
    }

    def __init__(self, *, min_value=None, max_value=None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        try:
            return self.type(value)
        except (TypeError, ValueError):
            return None

    @tornado.gen.coroutine
    def is_valid(self, value):
        value = yield self.to_internal_value(value)

        if value is None:
            self.fail('invalid')

        if self.min_value is not None and value < self.min_value:
            self.fail('min_value')

        if self.max_value is not None and value > self.max_value:
            self.fail('max_value')


class IntegerField(NumericField):

    type = int
    default_error_messages = {
        'invalid': 'Value must be a valid integer',
    }


class FloatField(NumericField):

    type = float
    default_error_messages = {
        'invalid': 'Value must be a valid float',
    }


class ChoiceField(Field):

    default_error_messages = {
        'invalid': 'Value must be in {choices}',
    }

    def __init__(self, *, choices, **kwargs):
        """Initialization instance.

        :param choices: choices.
        :type choices: iterable.
        """
        self.choices = list(choices)
        self.widget = inputs.Select(self.choices)
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def is_valid(self, value):
        choices = [choice[0] for choice in self.choices]

        if value not in choices:
            self.fail('invalid', choices=choices)


class ArrayField(TypedField):

    type = list
    widget = inputs.TextArea()
    default_error_messages = {
        'invalid': 'Value must be a valid array',
        'child': '{index}: {message}'
    }

    def __init__(self, *, field=None, **kwargs):
        self.field = field
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        try:
            yield self.is_valid(value)
        except ValidationError:
            return None

        if self.field:
            values = []

            for item in value:
                values.append((yield self.field.to_internal_value(item)))

            return values

        return value

    @tornado.gen.coroutine
    def is_valid(self, value):
        yield super().is_valid(value)

        if self.field:
            for index, item in enumerate(value):
                try:
                    yield self.field.validate(item)
                except ValidationError as e:
                    self.fail('child', index=index, message=e.error)


class MultipleChoiceField(ArrayField, ChoiceField):

    default_error_messages = {
        'choices': 'All values must be in {choices}',
    }

    def __init__(self, **kwargs):
        ChoiceField.__init__(self, **kwargs)
        ArrayField.__init__(self, **kwargs)

        self.widget.attributes['multiple'] = True

    @tornado.gen.coroutine
    def is_valid(self, value):
        yield ArrayField.is_valid(self, value)

        choices = [choice[0] for choice in self.choices]

        if any(choice not in choices for choice in value):
            self.fail('choices', choices=choices)


class URLField(StringField):

    default_error_messages = {
        'url': 'Value must be a valid URL',
    }

    @tornado.gen.coroutine
    def is_valid(self, value):
        yield super().is_valid(value)

        url = urllib.parse.urlparse(value)

        if not (url.scheme and url.netloc):
            self.fail('url')


class RegexMatchField(StringField):

    default_error_messages = {
        'pattern': 'Value must match by {0.pattern}',
    }

    def __init__(self, *, pattern=None, **kwargs):
        self.pattern = re.compile(pattern or self.pattern)
        super().__init__(**kwargs)

    @tornado.gen.coroutine
    def is_valid(self, value):
        yield super().is_valid(value)

        if not self.pattern.match(value):
            self.fail('pattern')


class HostField(RegexMatchField):

    default_error_messages = {
        'pattern': 'Value must be a valid host',
    }
    pattern = (
        # domain
        r'(?:[\w](?:[\w-]{0,61}[\w])?\.)+'
        r'(?:[A-Za-z]{2,6}\.?|[\w-]{2,}\.?$)'
        # ipv4 address
        r'|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    )


class SlugField(RegexMatchField):

    default_error_messages = {
        'pattern': 'Value must be a valid slug',
    }
    pattern = r'^[a-zA-Z\d\-_]+$'


class MapField(Field):

    widget = inputs.TextArea()
    default_error_messages = {
        'invalid': 'Value must be a map or JSON string',
    }

    @tornado.gen.coroutine
    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                return None

        return value

    @tornado.gen.coroutine
    def to_representation(self, value):
        return (yield self.to_internal_value(value))

    @tornado.gen.coroutine
    def is_valid(self, value):
        value = yield self.to_internal_value(value)

        if not isinstance(value, dict):
            self.fail('invalid')
