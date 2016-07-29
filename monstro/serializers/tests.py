# coding=utf-8

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.utils import Choice

from . import fields, serializer, exceptions


class FieldTest(monstro.testing.AsyncTestCase):

    def test_init(self):
        field = fields.IntegerField(default='1')

        self.assertEqual(field.default, '1')
        self.assertEqual(field.validators, [])

    def test_init__empty(self):
        field = fields.IntegerField()

        self.assertEqual(field.default, None)
        self.assertEqual(field.validators, [])

    @tornado.testing.gen_test
    def test__validation_error(self):
        field = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError):
            yield field.validate('a')

    @tornado.testing.gen_test
    def test__validation_error_required(self):
        field = fields.IntegerField(required=True)

        with self.assertRaises(exceptions.ValidationError):
            yield field.validate(None)

    @tornado.testing.gen_test
    def test__validation__validators(self):

        @tornado.gen.coroutine
        def validator(value):
            raise exceptions.ValidationError(value)

        field = fields.IntegerField(validators=[validator])

        with self.assertRaises(exceptions.ValidationError):
            yield field.validate(1)

    @tornado.testing.gen_test
    def test_not_implemented_error_on_call_is_valid(self):
        field = fields.Field()

        with self.assertRaises(NotImplementedError):
            yield field.validate(1)

    @tornado.testing.gen_test
    def test_get_metadata(self):
        field = fields.Field()

        self.assertEqual({
            'name': None,
            'label': None,
            'help_text': None,
            'required': True,
            'read_only': False,
            'default': None,
            'widget': None
        }, (yield field.get_metadata()))


class SerializerTest(monstro.testing.AsyncTestCase):

    def test_init__empty(self):
        with self.assertRaises(AssertionError):
            serializer.Serializer()

    def test_init__with_data(self):
        instance = serializer.Serializer(data={'name': 'test'})

        self.assertEqual({}, instance.__values__)

    def test_init__with_instance(self):
        class CustomSerializer(serializer.Serializer):

            name = fields.StringField()

        class Instance(object):

            name = 'test'

        instance = CustomSerializer(instance=Instance)

        self.assertEqual(instance.__values__['name'], 'test')

    def test_init__with_instance_and_data(self):
        with self.assertRaises(AssertionError):
            serializer.Serializer(instance='instance', data={'key': 'value'})

    def test_new(self):
        class CustomSerializer(serializer.Serializer):

            name = fields.StringField()

        self.assertIn('name', CustomSerializer.__fields__)

    def test_set_value(self):
        class CustomSerializer(serializer.Serializer):

            name = fields.StringField()

        instance = CustomSerializer(data={'name': ''})
        instance.name = 'test'

        self.assertEqual(instance.name, 'test')

    @tornado.testing.gen_test
    def test_getattr__attribute_error(self):
        class CustomSerializer(serializer.Serializer):

            name = fields.StringField()

        instance = CustomSerializer(data={'name': 'test'})

        with self.assertRaises(AttributeError):
            instance.none()

    @tornado.testing.gen_test
    def test_construct(self):
        class CustomSerializer(serializer.Serializer):

            map = fields.MapField()

        instance = CustomSerializer(data={'map': '{"name": "test"}'})

        yield instance.construct()

        self.assertEqual(instance.map['name'], 'test')

    @tornado.testing.gen_test
    def test_validate(self):
        class CustomSerializer(serializer.Serializer):
            __collection__ = 'test'

            string = fields.StringField()

        instance = CustomSerializer(data={'string': 'test'})

        data = yield instance.validate()

        self.assertEqual(data['string'], 'test')

    @tornado.testing.gen_test
    def test_validate__error(self):
        class CustomSerializer(serializer.Serializer):
            __collection__ = 'test'

            string = fields.StringField()

        instance = CustomSerializer(data={'string': 1})

        with self.assertRaises(exceptions.ValidationError) as context:
            yield instance.validate()

        self.assertIn('string', context.exception.error)

    @tornado.testing.gen_test
    def test__read_only(self):

        class CustomSerializer(serializer.Serializer):
            __collection__ = 'test'

            string = fields.StringField(read_only=True)

        instance = CustomSerializer(data={'string': '1'})

        with self.assertRaises(exceptions.ValidationError) as context:
            yield instance.validate()

        self.assertEqual(
            instance.__fields__['string'].error_messages['read_only'],
            context.exception.error['string']
        )

    @tornado.testing.gen_test
    def test_get_metadata(self):
        class CustomSerializer(serializer.Serializer):
            __collection__ = 'test'

            string = fields.StringField(
                label='Label', help_text='Help', default='default'
            )

        instance = CustomSerializer(data={'string': 1})

        self.assertEqual([{
            'name': 'string',
            'label': 'Label',
            'help_text': 'Help',
            'required': True,
            'read_only': False,
            'default': 'default',
            'widget': {
                'attrs': {'type': 'text'},
                'is_pair': False,
                'tag': 'input',
            }
        }], (yield instance.get_metadata()))

    @tornado.testing.gen_test
    def test_get_data(self):
        class CustomSerializer(serializer.Serializer):
            __collection__ = 'test'

            string = fields.StringField(
                label='Label', help_text='Help', default='default'
            )

        instance = CustomSerializer(data={'string': '1'})

        self.assertEqual({'string': '1'}, (yield instance.get_data()))


class BooleanFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.BooleanField()
        self.assertTrue((yield field.validate(True)))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.BooleanField()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.BooleanField.default_error_messages['invalid']
        )


class StringFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.StringField()
        self.assertEqual('Test', (yield field.validate('Test')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.StringField()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(10)

        self.assertEqual(
            context.exception.error,
            fields.StringField.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_length(self):
        field = fields.StringField(min_length=5, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.StringField.default_error_messages['min_length'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_length(self):
        field = fields.StringField(max_length=3, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.StringField.default_error_messages['max_length'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_to_internal_value__none(self):
        field = fields.StringField()

        self.assertEqual(None, (yield field.to_internal_value(None)))


class IntegerFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.IntegerField()
        self.assertEqual(10, (yield field.validate('10')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.IntegerField.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_value(self):
        field = fields.IntegerField(default=10, min_value=11)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.NumericField.default_error_messages['min_value'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_value(self):
        field = fields.IntegerField(default=10, max_value=9)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.NumericField.default_error_messages['max_value'].format(
                field
            )
        )


class FloatFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.FloatField()
        self.assertEqual(10.2, (yield field.validate('10.2')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.FloatField()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.FloatField.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_value(self):
        field = fields.FloatField(default=10.1, min_value=10.2)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.NumericField.default_error_messages['min_value'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_value(self):
        field = fields.FloatField(default=10.11, max_value=10.10)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.NumericField.default_error_messages['max_value'].format(
                field
            )
        )


class ChoiceFieldTest(monstro.testing.AsyncTestCase):

    choices = Choice(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.ChoiceField(choices=self.choices.choices)
        self.assertEqual('a', (yield field.validate('a')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.ChoiceField(default='c', choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.ChoiceField.default_error_messages['invalid'].format(
                choices=self.choices.values
            )
        )


class MultipleChoiceFieldTest(monstro.testing.AsyncTestCase):

    choices = Choice(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.MultipleChoiceField(choices=self.choices.choices)
        self.assertEqual(['a'], (yield field.validate(['a'])))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.MultipleChoiceField(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('c')

        self.assertEqual(
            context.exception.error,
            fields.ArrayField.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_validate__choices(self):
        field = fields.MultipleChoiceField(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(['c'])

        self.assertEqual(
            context.exception.error,
            fields.MultipleChoiceField \
                .default_error_messages['choices'] \
                .format(choices=self.choices.values)
        )


class ArrayFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.ArrayField(field=fields.IntegerField())
        self.assertEqual([10], (yield field.validate(['10'])))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.ArrayField(default='string')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.ArrayField.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_to_internal_value__invalid(self):
        field = fields.ArrayField()

        self.assertEqual(None, (yield field.to_internal_value('wrong')))

    @tornado.testing.gen_test
    def test_validate__invalid_item(self):
        field = fields.ArrayField(default=['j'], field=fields.IntegerField())

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.ArrayField.default_error_messages['child'].format(
                index=0,
                message=fields.IntegerField.default_error_messages['invalid']
            )
        )


class URLFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.URLField()
        self.assertEqual(
            'https://pyvim.com/about/',
            (yield field.validate('https://pyvim.com/about/'))
        )

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.URLField(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.StringField.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.URLField(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.URLField.default_error_messages['url']
        )


class HostFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate_ip(self):
        field = fields.HostField()
        self.assertEqual(
            '144.76.78.182', (yield field.validate('144.76.78.182'))
        )

    @tornado.testing.gen_test
    def test_validate_url(self):
        field = fields.HostField()
        self.assertEqual('pyvim.com', (yield field.validate('pyvim.com')))

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.HostField(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.StringField.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.HostField(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.HostField.default_error_messages['pattern'].format(field)
        )


class MapFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.MapField()
        self.assertEqual(
            {'key': 'value'}, (yield field.validate({'key': 'value'}))
        )

    @tornado.testing.gen_test
    def test_validate__invalid_json(self):
        field = fields.MapField(default='wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.MapField.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_to_internal_value__invalid_json(self):
        field = fields.MapField()

        self.assertEqual(None, (yield field.to_internal_value('wrong')))

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.MapField(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.MapField.default_error_messages['invalid'].format(field)
        )


class SlugFieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.SlugField()
        self.assertEqual(
            'back-jack-100_1', (yield field.validate('back-jack-100_1'))
        )

    @tornado.testing.gen_test
    def test_validate__error(self):
        field = fields.SlugField(default='wrong slug')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.SlugField.default_error_messages['pattern'].format(field)
        )
