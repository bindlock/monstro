import collections

from .exceptions import ValidationError
from .fields import Field


class MetaForm(type):

    @classmethod
    def __prepare__(mcs, *args, **kwargs):
        return collections.OrderedDict()

    def __new__(mcs, name, bases, attributes):
        fields = collections.OrderedDict()

        for parent in bases:
            if hasattr(parent, 'Meta'):
                fields.update(parent.Meta.fields)

        for key, value in list(attributes.items()):
            if isinstance(value, Field):
                value.bind(name=key)
                fields[key] = value
                attributes.pop(key, None)

        attributes.setdefault('Meta', type('Meta', (), {}))

        cls = type.__new__(mcs, name, bases, attributes)

        cls.Meta.fields = fields
        cls.ValidationError = ValidationError

        return cls


class MetaModelForm(MetaForm):

    def __new__(mcs, name, bases, attributes):
        if 'Meta' in attributes:
            Meta = attributes['Meta']
            fields = getattr(Meta, 'fields', Meta.model.Meta.fields.keys())

            for field in fields:
                attributes.setdefault(field, Meta.model.Meta.fields[field])

        return super().__new__(mcs, name, bases, attributes)


class Form(object, metaclass=MetaForm):

    def __init__(self, data):
        self.data = data
        self.errors = {}

    @classmethod
    async def get_options(cls):
        metadata = []

        for field in cls.Meta.fields.values():
            metadata.append(await field.get_options())

        return metadata

    async def is_valid(self):
        try:
            await self.validate()
        except self.ValidationError as e:
            if isinstance(e.error, dict):
                self.errors = e.error
            elif isinstance(e.error, str):
                self.errors['common'] = e.error
        finally:
            return not bool(self.errors)  # pylint:disable=W0150

    async def validate(self):
        for name, field in self.Meta.fields.items():
            value = self.data.get(name)

            try:
                self.data[name] = await field.validate(value)
            except ValidationError as e:
                self.errors[name] = e.error

        if self.errors:
            raise self.ValidationError(self.errors)

    async def serialize(self, raw_fields=()):
        raw_fields = raw_fields or getattr(self.Meta, 'raw_fields', ())
        data = {}

        for name, field in self.Meta.fields.items():
            value = self.data.get(name)

            if value is None or name in raw_fields:
                data[name] = value
            else:
                data[name] = await field.serialize(value)

        return data


class ModelForm(Form, metaclass=MetaModelForm):

    def __init__(self, *, instance=None, data=None):
        super().__init__(data or {})

        self.instance = instance or self.Meta.model()

        for name, field in self.Meta.fields.items():
            value = self.data.get(name, getattr(instance, name, field.default))
            self.data[name] = value

    async def validate(self):
        for name, field in self.Meta.fields.items():
            if field.read_only:
                self.data[name] = getattr(self.instance, name, field.default)
                continue

            value = self.data.get(name)

            try:
                self.data[name] = await field.validate(value)
            except ValidationError as e:
                self.errors[name] = e.error

        if self.errors:
            raise self.ValidationError(self.errors)

    async def save(self):
        self.data['_id'] = self.instance._id
        self.instance = self.Meta.model(**self.data)
        await self.instance.save()

        for name in self.Meta.fields.keys():
            self.data[name] = getattr(self.instance, name)

        return self.instance

    async def serialize(self, raw_fields=()):
        raw_fields = (
            raw_fields
            or getattr(getattr(self.instance, 'Meta', {}), 'raw_fields', ())
        )

        return await super().serialize(raw_fields)
