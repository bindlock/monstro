# coding=utf-8

import datetime

import tornado.gen

import monstro.testing
from monstro.utils import Choices

from monstro.forms import fields, exceptions


class FieldTest(monstro.testing.AsyncTestCase):

    async def test_to_python(self):
        field = fields.Field()

        self.assertEqual(None, await field.to_python(None))

    async def test_to_internal_value(self):
        field = fields.Field()

        self.assertEqual(None, await field.to_internal_value(None))

    def test_callable_default(self):
        field = fields.Integer(default=lambda: 1 + 1)

        self.assertEqual(2, field.default)

    def test_coroutine_default(self):

        @tornado.gen.coroutine
        def f():
            return 1 + 1

        field = fields.Integer(default=f)

        self.assertEqual(2, field.default)

    async def test__validation_error(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('a')

        self.assertEqual(
            context.exception.error,
            fields.Integer.error_messages['invalid']
        )

    async def test__validation_error_required(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Field.error_messages['required']
        )

    async def test_validation__validators(self):

        async def validator(value):
            raise exceptions.ValidationError(value)

        field = fields.Integer(validators=[validator])

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(1)

        self.assertEqual(context.exception.error, 1)

    async def test_get_metadata(self):
        field = fields.Field()

        self.assertEqual({
            'name': None,
            'label': None,
            'help_text': None,
            'required': True,
            'read_only': False,
            'default': None,
            'widget': None
        }, await field.get_metadata())


class BooleanTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Boolean()
        self.assertTrue(await field.validate(True))

    async def test_validate__invalid(self):
        field = fields.Boolean()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Boolean.error_messages['invalid']
        )


class StringTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.String()
        self.assertEqual('Test', await field.validate('Test'))

    async def test_validate__invalid(self):
        field = fields.String()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(10)

        self.assertEqual(
            context.exception.error,
            fields.String.error_messages['invalid']
        )

    async def test_validate__min_length(self):
        field = fields.String(min_length=5, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.error_messages['min_length'].format(
                field
            )
        )

    async def test_validate__max_length(self):
        field = fields.String(max_length=3, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.error_messages['max_length'].format(
                field
            )
        )

    async def test_to_internal_value__none(self):
        field = fields.String()

        self.assertEqual(None, await field.to_internal_value(None))


class IntegerTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Integer()
        self.assertEqual(10, await field.validate('10'))

    async def test_validate__invalid(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Integer.error_messages['invalid']
        )

    async def test_validate__min_value(self):
        field = fields.Integer(default=10, min_value=11)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.error_messages['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Integer(default=10, max_value=9)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.error_messages['max_value'].format(
                field
            )
        )


class FloatTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Float()
        self.assertEqual(10.2, await field.validate('10.2'))

    async def test_validate__invalid(self):
        field = fields.Float()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.Float.error_messages['invalid']
        )

    async def test_validate__min_value(self):
        field = fields.Float(default=10.1, min_value=10.2)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.error_messages['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Float(default=10.11, max_value=10.10)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.error_messages['max_value'].format(
                field
            )
        )


class ChoicesTest(monstro.testing.AsyncTestCase):

    choices = Choices(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    async def test_validate(self):
        field = fields.Choice(choices=self.choices.choices)
        self.assertEqual('a', await field.validate('a'))

    async def test_validate__invalid(self):
        field = fields.Choice(default='c', choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Choice.error_messages['invalid'].format(
                choices=self.choices.values
            )
        )


class MultipleChoiceTest(monstro.testing.AsyncTestCase):

    choices = Choices(
        ('A', 'a', 'A'),
        ('B', 'b', 'B'),
    )

    async def test_validate(self):
        field = fields.MultipleChoice(choices=self.choices.choices)
        self.assertEqual(['a'], await field.validate(['a']))

    async def test_validate__invalid(self):
        field = fields.MultipleChoice(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('c')

        self.assertEqual(
            context.exception.error,
            fields.Array.error_messages['invalid'].format(field)
        )

    async def test_validate__choices(self):
        field = fields.MultipleChoice(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(['c'])

        self.assertEqual(
            context.exception.error,
            fields.MultipleChoice \
                .error_messages['choices'] \
                .format(choices=self.choices.values)
        )


class ArrayTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Array(field=fields.Integer())
        self.assertEqual([10], await field.validate(['10']))

    async def test_validate__invalid(self):
        field = fields.Array(default='string')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Array.error_messages['invalid'].format(field)
        )

    async def test_validate__invalid_item(self):
        field = fields.Array(default=['j'], field=fields.Integer())

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Array.error_messages['child'].format(
                index=0,
                message=fields.Integer.error_messages['invalid']
            )
        )

    async def test_to_python(self):
        field = fields.Array()

        self.assertEqual([], await field.to_python([]))

    async def test_to_python__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], await field.to_python(['1']))

    async def test_to_internal_value(self):
        field = fields.Array()

        self.assertEqual([1], await field.to_internal_value([1]))

    async def test_to_internal_value__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], await field.to_internal_value([1]))


class URLTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.URL()
        self.assertEqual(
            'https://pyvim.com/about/',
            await field.validate('https://pyvim.com/about/')
        )

    async def test_validate__invalid_type(self):
        field = fields.URL(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.error_messages['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.URL(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.URL.error_messages['url']
        )


class HostTest(monstro.testing.AsyncTestCase):

    async def test_validate_ip(self):
        field = fields.Host()
        self.assertEqual(
            '144.76.78.182', await field.validate('144.76.78.182')
        )

    async def test_validate_url(self):
        field = fields.Host()
        self.assertEqual('pyvim.com', await field.validate('pyvim.com'))

    async def test_validate__invalid_type(self):
        field = fields.Host(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.error_messages['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.Host(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Host.error_messages['pattern'].format(field)
        )


class MapTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Map()
        self.assertEqual(
            {'key': 'value'}, await field.validate({'key': 'value'})
        )

    async def test_validate__invalid_type(self):
        field = fields.Map(default=5)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Map.error_messages['invalid'].format(field)
        )


class JSONTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.JSON()
        self.assertEqual(
            {'key': 'value'}, await field.validate('{"key": "value"}')
        )

    async def test_validate__invalid_type(self):
        field = fields.JSON()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(5)

        self.assertEqual(
            context.exception.error,
            fields.JSON.error_messages['invalid'].format(field)
        )


class SlugTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Slug()
        self.assertEqual(
            'back-jack-100_1', await field.validate('back-jack-100_1')
        )

    async def test_validate__error(self):
        field = fields.Slug(default='wrong slug')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Slug.error_messages['pattern'].format(field)
        )


class DateTimeTest(monstro.testing.AsyncTestCase):

    async def test_on_save(self):
        field = fields.DateTime(auto_now=True)
        self.assertIsInstance(await field.on_save(None), datetime.datetime)

    async def test_on_save__without_auto(self):
        field = fields.DateTime()

        self.assertEqual(None, await field.on_save(None))

    async def test_on_create(self):
        field = fields.DateTime(auto_now_on_create=True)

        self.assertIsInstance(await field.on_create(None), datetime.datetime)

    async def test_on_create__without_auto(self):
        field = fields.DateTime()

        self.assertEqual(await field.on_create(None), None)

    async def test_to_internal_value(self):
        field = fields.DateTime()

        self.assertEqual(
            '2015-07-13T00:00:00',
            await field.to_internal_value(datetime.datetime(2015, 7, 13))
        )

    async def test_to_python(self):
        field = fields.DateTime()

        self.assertIsInstance(
            await field.to_python('2015-07-13T14:08:12.000000'),
            datetime.datetime
        )

    async def test_to_python__wrong_format(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.to_python('wrong')

        self.assertEqual(
            context.exception.error,
            field.error_messages['invalid'].format(field)
        )

    async def test_to_python__wrong_object(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.to_python(object)

        self.assertEqual(
            context.exception.error,
            field.error_messages['invalid'].format(field)
        )


class DateTest(monstro.testing.AsyncTestCase):

    async def test_to_internal_value(self):
        field = fields.Date()

        self.assertEqual(
            '2015-07-13',
            await field.to_internal_value(datetime.date(2015, 7, 13))
        )

    async def test_to_python(self):
        field = fields.Date()

        self.assertIsInstance(
            await field.to_python('2015-07-13'), datetime.date
        )


class TimeTest(monstro.testing.AsyncTestCase):

    async def test_to_internal_value(self):
        field = fields.Time()

        self.assertEqual(
            '00:00:00', await field.to_internal_value(datetime.time())
        )

    async def test_to_python(self):
        field = fields.Time()

        self.assertIsInstance(
            await field.to_python('14:08:12'), datetime.time
        )
