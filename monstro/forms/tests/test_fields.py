# coding=utf-8

import datetime

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.utils import Choices

from monstro.forms import fields, exceptions


class FieldTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_to_python(self):
        field = fields.Field()

        self.assertEqual(None, (yield field.to_python(None)))

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        field = fields.Field()

        self.assertEqual(None, (yield field.to_internal_value(None)))

    @tornado.testing.gen_test
    def test_callable_default(self):
        field = fields.Integer(default=lambda: 1 + 1)

        self.assertEqual(2, field.default)

    @tornado.testing.gen_test
    def test_coroutine_default(self):

        @tornado.gen.coroutine
        def f():
            return 1 + 1

        field = fields.Integer(default=f)

        self.assertEqual(2, field.default)

    @tornado.testing.gen_test
    def test__validation_error(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('a')

        self.assertEqual(
            context.exception.error,
            fields.Integer.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test__validation_error_required(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Field.default_error_messages['required']
        )

    @tornado.testing.gen_test
    def test_validation__validators(self):

        @tornado.gen.coroutine
        def validator(value):
            raise exceptions.ValidationError(value)

        field = fields.Integer(validators=[validator])

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(1)

        self.assertEqual(context.exception.error, 1)

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


class BooleanTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Boolean()
        self.assertTrue((yield field.validate(True)))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Boolean()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Boolean.default_error_messages['invalid']
        )


class StringTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.String()
        self.assertEqual('Test', (yield field.validate('Test')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.String()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(10)

        self.assertEqual(
            context.exception.error,
            fields.String.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_length(self):
        field = fields.String(min_length=5, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.default_error_messages['min_length'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_length(self):
        field = fields.String(max_length=3, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.default_error_messages['max_length'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_to_internal_value__none(self):
        field = fields.String()

        self.assertEqual(None, (yield field.to_internal_value(None)))


class IntegerTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Integer()
        self.assertEqual(10, (yield field.validate('10')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Integer.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_value(self):
        field = fields.Integer(default=10, min_value=11)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.default_error_messages['min_value'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_value(self):
        field = fields.Integer(default=10, max_value=9)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.default_error_messages['max_value'].format(
                field
            )
        )


class FloatTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Float()
        self.assertEqual(10.2, (yield field.validate('10.2')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Float()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Float.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__min_value(self):
        field = fields.Float(default=10.1, min_value=10.2)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.default_error_messages['min_value'].format(
                field
            )
        )

    @tornado.testing.gen_test
    def test_validate__max_value(self):
        field = fields.Float(default=10.11, max_value=10.10)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.default_error_messages['max_value'].format(
                field
            )
        )


class ChoicesTest(monstro.testing.AsyncTestCase):

    choices = Choices(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Choice(choices=self.choices.choices)
        self.assertEqual('a', (yield field.validate('a')))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Choice(default='c', choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Choice.default_error_messages['invalid'].format(
                choices=self.choices.values
            )
        )


class MultipleChoiceTest(monstro.testing.AsyncTestCase):

    choices = Choices(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.MultipleChoice(choices=self.choices.choices)
        self.assertEqual(['a'], (yield field.validate(['a'])))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.MultipleChoice(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate('c')

        self.assertEqual(
            context.exception.error,
            fields.Array.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_validate__choices(self):
        field = fields.MultipleChoice(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate(['c'])

        self.assertEqual(
            context.exception.error,
            fields.MultipleChoice \
                .default_error_messages['choices'] \
                .format(choices=self.choices.values)
        )


class ArrayTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Array(field=fields.Integer())
        self.assertEqual([10], (yield field.validate(['10'])))

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Array(default='string')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Array.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_validate__invalid_item(self):
        field = fields.Array(default=['j'], field=fields.Integer())

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Array.default_error_messages['child'].format(
                index=0,
                message=fields.Integer.default_error_messages['invalid']
            )
        )

    @tornado.testing.gen_test
    def test_to_python(self):
        field = fields.Array()

        self.assertEqual([], (yield field.to_python([])))

    @tornado.testing.gen_test
    def test_to_python__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], (yield field.to_python(['1'])))

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        field = fields.Array()

        self.assertEqual([1], (yield field.to_internal_value([1])))

    @tornado.testing.gen_test
    def test_to_internal_value__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], (yield field.to_internal_value([1])))


class UrlTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Url()
        self.assertEqual(
            'https://pyvim.com/about/',
            (yield field.validate('https://pyvim.com/about/'))
        )

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.Url(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Url(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Url.default_error_messages['url']
        )


class HostTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate_ip(self):
        field = fields.Host()
        self.assertEqual(
            '144.76.78.182', (yield field.validate('144.76.78.182'))
        )

    @tornado.testing.gen_test
    def test_validate_url(self):
        field = fields.Host()
        self.assertEqual('pyvim.com', (yield field.validate('pyvim.com')))

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.Host(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__invalid(self):
        field = fields.Host(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Host.default_error_messages['pattern'].format(field)
        )


class MapTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Map()
        self.assertEqual(
            {'key': 'value'}, (yield field.validate({'key': 'value'}))
        )

    @tornado.testing.gen_test
    def test_validate__invalid_json(self):
        field = fields.Map(default='wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Map.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_validate__invalid_type(self):
        field = fields.Map(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Map.default_error_messages['invalid'].format(field)
        )


class SlugTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_validate(self):
        field = fields.Slug()
        self.assertEqual(
            'back-jack-100_1', (yield field.validate('back-jack-100_1'))
        )

    @tornado.testing.gen_test
    def test_validate__error(self):
        field = fields.Slug(default='wrong slug')

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Slug.default_error_messages['pattern'].format(field)
        )


class DateTimeTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_init__auto_now_on_create(self):
        field = fields.DateTime(auto_now_on_create=True)

        self.assertTrue(field.default)
        self.assertIsInstance((yield field.validate(None)), datetime.datetime)

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        field = fields.DateTime()

        self.assertEqual(
            '2015-07-13T00:00:00',
            (yield field.to_internal_value(datetime.datetime(2015, 7, 13)))
        )

    @tornado.testing.gen_test
    def test_validate__auto_now(self):
        field = fields.DateTime(auto_now=True)

        self.assertTrue(field.auto_now)
        self.assertTrue((yield field.validate(None)))

    @tornado.testing.gen_test
    def test_to_python(self):
        field = fields.DateTime()

        self.assertIsInstance(
            (yield field.to_python('2015-07-13T14:08:12')),
            datetime.datetime
        )

    @tornado.testing.gen_test
    def test_to_python__wrong_format(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.to_python('wrong')

        self.assertEqual(
            context.exception.error,
            field.error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_to_python__wrong_object(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            yield field.to_python(object)

        self.assertEqual(
            context.exception.error,
            field.error_messages['invalid'].format(field)
        )


class DateTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_init__auto_now_on_create(self):
        field = fields.Date(auto_now_on_create=True)

        self.assertTrue(field.default)
        self.assertTrue((yield field.validate(None)))

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        field = fields.Date()

        self.assertEqual(
            '2015-07-13',
            (yield field.to_internal_value(datetime.date(2015, 7, 13)))
        )

    @tornado.testing.gen_test
    def test_to_internal_value__auto_now(self):
        field = fields.Date(auto_now=True)

        self.assertTrue((yield field.to_internal_value(None)))

    @tornado.testing.gen_test
    def test_to_python(self):
        field = fields.Date()

        self.assertIsInstance(
            (yield field.to_python('2015-07-13')), datetime.date
        )


class TimeTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_init__auto_now_on_create(self):
        field = fields.Time(auto_now_on_create=True)

        self.assertTrue(field.default)
        self.assertTrue((yield field.validate(None)))

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        field = fields.Time()

        self.assertEqual(
            '00:00:00', (yield field.to_internal_value(datetime.time()))
        )

    @tornado.testing.gen_test
    def test_to_internal_value__auto_now(self):
        field = fields.Time(auto_now=True)

        self.assertTrue((yield field.to_internal_value(None)))

    @tornado.testing.gen_test
    def test_to_python(self):
        field = fields.Time()

        self.assertIsInstance(
            (yield field.to_python('14:08:12')), datetime.time
        )
