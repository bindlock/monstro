# coding=utf-8

import re
import json
import datetime
import urllib.parse

from . import widgets
from .exceptions import ValidationError


__all__ = (
    'Field',
    'Boolean',
    'String',
    'Integer',
    'Float',
    'Choice',
    'Array',
    'MultipleChoice',
    'URL',
    'RegexMatch',
    'Host',
    'Slug',
    'Map',
    'JSON',
    'Date',
    'Time',
    'DateTime'
)


class Field(object):

    widget = None
    error_messages = {
        'required': 'Value is required',
        'invalid': 'Value is invalid',
        'unique': 'Value must be unique',
        'read_only': 'Read-only field'
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
        :param error_messages (optional): override default error messages.
        :type error_messages: dict.
        """
        self.name = name
        self.required = required
        self._default = default
        self._label = label
        self.unique = unique
        self.help_text = help_text
        self.read_only = read_only
        self.validators = validators or []
        self.widget = widget or self.widget

        if self._default is not None:
            self.required = False

        messages = {}

        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'error_messages', {}))

        messages.update(error_messages or {})

        self.error_messages = messages

    @property
    def label(self):
        if self._label is None and self.name is not None:
            self._label = ' '.join(re.split(r'[\W_]', self.name)).capitalize()

        return self._label

    @property
    def default(self):
        if callable(self._default):
            return self._default()

        return self._default

    def bind(self, **kwargs):
        self.__dict__.update(kwargs)

    async def validate(self, value=None, model=None):
        if value is None:
            value = self.default

        if value is None:
            if self.required:
                self.fail('required')
            else:
                return None

        value = await self.to_python(value)

        for validator in self.validators:
            value = await validator(value)

        if self.unique and hasattr(self, 'model'):
            try:
                instance = await self.model.objects.get(**{self.name: value})
            except self.model.DoesNotExist:
                instance = None

            if instance and model and instance._id != model._id:
                self.fail('unique')

        return value

    def fail(self, error_code, **kwargs):
        raise ValidationError(
            self.error_messages[error_code].format(self, **kwargs), self.name
        )

    async def to_python(self, value):
        return value

    async def to_internal_value(self, value):
        return value

    async def on_save(self, value):
        return value

    async def on_create(self, value):
        return value

    async def get_options(self):
        metadata = {
            'name': self.name,
            'label': self.label or (self.name and self.name.title()),
            'help_text': self.help_text,
            'required': self.required,
            'read_only': self.read_only,
        }

        if not (self._default is None or callable(self._default)):
            metadata['default'] = await self.to_internal_value(self._default)
        else:
            metadata['default'] = None

        if self.widget:
            metadata['widget'] = self.widget.get_options()
        else:
            metadata['widget'] = None

        return metadata


class Type(Field):

    type = type
    widget = widgets.Input('text')
    error_messages = {
        'invalid': 'Value must be a valid {0.type.__name__}'
    }

    async def to_python(self, value):
        if not isinstance(value, self.type):
            self.fail('invalid')

        return value


class Boolean(Type):

    type = bool
    widget = widgets.Input('checkbox')
    error_messages = {
        'invalid': 'Value must be a valid boolean'
    }


class String(Type):

    type = str
    error_messages = {
        'invalid': 'Value must be a valid string',
        'min_length': 'String must be greater {0.min_length} characters',
        'max_length': 'String must be less {0.max_length} characters'
    }

    def __init__(self, *, min_length=None, max_length=None, **kwargs):
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(**kwargs)

    async def to_python(self, value):
        value = await super().to_python(value)

        if self.min_length is not None and len(value) < self.min_length:
            self.fail('min_length')

        if self.max_length is not None and len(value) > self.max_length:
            self.fail('max_length')

        return value


class Numeric(Type):

    error_messages = {
        'invalid': 'Value must be a valid integer or float',
        'min_value': 'Number must be greater {0.min_value} characters',
        'max_value': 'Number must be less {0.max_value} characters'
    }

    def __init__(self, *, min_value=None, max_value=None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(**kwargs)

    async def to_python(self, value):
        try:
            value = self.type(value)
        except (TypeError, ValueError):
            self.fail('invalid')

        if self.min_value is not None and value < self.min_value:
            self.fail('min_value')

        if self.max_value is not None and value > self.max_value:
            self.fail('max_value')

        return value


class Integer(Numeric):

    type = int
    error_messages = {
        'invalid': 'Value must be a valid integer',
    }


class Float(Numeric):

    type = float
    error_messages = {
        'invalid': 'Value must be a valid float',
    }


class Choice(Field):

    error_messages = {
        'invalid': 'Value must be in {choices}',
    }

    def __init__(self, *, choices, **kwargs):
        """Initialization instance.

        :param choices: choices.
        :type choices: iterable.
        """
        self.choices = list(choices)
        self.widget = widgets.Select(self.choices)
        super().__init__(**kwargs)

    async def to_python(self, value):
        choices = [choice[0] for choice in self.choices]

        if value not in choices:
            self.fail('invalid', choices=choices)

        return value


class Array(Type):

    type = list
    widget = widgets.TextArea()
    error_messages = {
        'invalid': 'Value must be a valid array',
        'child': '{index}: {message}'
    }

    def __init__(self, *, field=None, **kwargs):
        self.field = field
        super().__init__(**kwargs)

    async def to_python(self, value):
        value = await super().to_python(value)

        if self.field:
            values = []

            for index, item in enumerate(value):
                try:
                    values.append(await self.field.to_python(item))
                except ValidationError as e:
                    self.fail('child', index=index, message=e.error)

            return values

        return value

    async def to_internal_value(self, value):
        if self.field:
            values = []

            for item in value:
                values.append(await self.field.to_internal_value(item))

            return values

        return value


class MultipleChoice(Array, Choice):

    error_messages = {
        'choices': 'All values must be in {choices}',
    }

    def __init__(self, **kwargs):
        Choice.__init__(self, **kwargs)
        Array.__init__(self, **kwargs)

        self.widget.attributes['multiple'] = True

    async def to_python(self, value):
        value = await Array.to_python(self, value)

        choices = [choice[0] for choice in self.choices]

        if any(choice not in choices for choice in value):
            self.fail('choices', choices=choices)

        return value


class URL(String):

    error_messages = {
        'url': 'Value must be a valid URL',
    }

    async def to_python(self, value):
        value = await super().to_python(value)

        url = urllib.parse.urlparse(value)

        if not (url.scheme and url.netloc):
            self.fail('url')

        return value


class RegexMatch(String):

    error_messages = {
        'pattern': 'Value must match by {0.pattern}',
    }

    def __init__(self, *, pattern=None, **kwargs):
        self.pattern = re.compile(pattern or self.pattern)
        super().__init__(**kwargs)

    async def to_python(self, value):
        value = await super().to_python(value)

        if not self.pattern.match(value):
            self.fail('pattern')

        return value


class Host(RegexMatch):

    error_messages = {
        'pattern': 'Value must be a valid host',
    }
    pattern = (
        # domain
        r'(?:[\w](?:[\w-]{0,61}[\w])?\.)+'
        r'(?:[A-Za-z]{2,6}\.?|[\w-]{2,}\.?$)'
        # ipv4 address
        r'|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    )


class Slug(RegexMatch):

    error_messages = {
        'pattern': 'Value must be a valid slug',
    }
    pattern = r'^[a-zA-Z\d\-_]+$'


class Map(Field):

    widget = widgets.TextArea()
    error_messages = {
        'invalid': 'Value must be a map',
    }

    async def to_python(self, value):
        if not isinstance(value, dict):
            self.fail('invalid')

        return value


class JSON(Field):

    widget = widgets.TextArea()
    error_messages = {
        'invalid': 'Value must be a valid JSON string',
    }

    async def to_python(self, value):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            self.fail('invalid')


class DateTime(Field):

    widget = widgets.Input('datetime')
    error_messages = {
        'invalid': 'Datetime must be in next formats: {0.available_formats}'
    }

    default_format = '%Y-%m-%dT%H:%M:%S.%f'

    def __init__(self, *, input_formats=None, output_format=None,
                 auto_now=False, auto_now_on_create=False, **kwargs):

        super().__init__(**kwargs)
        self.input_formats = input_formats or []
        self.output_format = output_format
        self.auto_now = auto_now
        self.auto_now_on_create = auto_now_on_create

        if self.auto_now or self.auto_now_on_create:
            self.required = False

        self.widget.attributes['format'] = self.output_format

    @property
    def available_formats(self):
        return list(set(self.input_formats + [self.default_format]))

    async def on_save(self, value):
        if self.auto_now:
            return datetime.datetime.now()

        return value

    async def on_create(self, value):
        if self.auto_now_on_create:
            return datetime.datetime.now()

        return value

    async def to_python(self, value):
        if isinstance(value, str):
            for input_format in self.available_formats:
                try:
                    value = datetime.datetime.strptime(value, input_format)
                    break
                except ValueError:
                    continue
            else:
                self.fail('invalid')
        elif not hasattr(value, 'strftime'):
            self.fail('invalid')

        return value

    async def to_internal_value(self, value):
        return value.isoformat()


class Date(DateTime):

    widget = widgets.Input('date')
    error_messages = {
        'invalid': 'Date must be in next formats: {0.available_formats}'
    }

    default_format = '%Y-%m-%d'

    async def to_python(self, value):
        return (await super().to_python(value)).date()


class Time(DateTime):

    widget = widgets.Input('time')
    error_messages = {
        'invalid': 'Time must be in next formats: {0.available_formats}'
    }

    default_format = '%H:%M:%S'

    async def to_python(self, value):
        return (await super().to_python(value)).time()
