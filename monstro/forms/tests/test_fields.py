import datetime

import monstro.testing
from monstro.utils import Choices

from monstro.forms import fields, exceptions


class FieldTest(monstro.testing.AsyncTestCase):

    async def test_deserialize(self):
        field = fields.Field()

        self.assertEqual(None, await field.deserialize(None))

    async def test_serialize(self):
        field = fields.Field()

        self.assertEqual(None, field.serialize(None))

    def test_create_label_from_name(self):
        field = fields.Field(name='some_field')

        self.assertEqual('Some field', field.label)

    def test_callable_default(self):
        field = fields.Integer(default=lambda: 1 + 1)

        self.assertEqual(2, field.default)

    async def test__validation_error(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate('a')

        self.assertEqual(
            context.exception.error,
            fields.Integer.errors['invalid']
        )

    async def test__validation_error_required(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Field.errors['required']
        )

    async def test_validation__validators(self):

        async def validator(value):
            raise exceptions.ValidationError(value)

        field = fields.Integer(validators=[validator])

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(1)

        self.assertEqual(context.exception.error, 1)

    async def test_get_options(self):
        field = fields.Field()

        self.assertEqual({
            'name': None,
            'label': None,
            'help_text': None,
            'required': True,
            'read_only': False,
            'default': None,
            'widget': None
        }, await field.get_options())


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
            fields.Boolean.errors['invalid']
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
            fields.String.errors['invalid']
        )

    async def test_validate__min_length(self):
        field = fields.String(min_length=5, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.errors['min_length'].format(
                field
            )
        )

    async def test_validate__max_length(self):
        field = fields.String(max_length=3, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.String.errors['max_length'].format(
                field
            )
        )

    async def test_serialize__none(self):
        field = fields.String()

        self.assertEqual(None, field.serialize(None))


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
            fields.Integer.errors['invalid']
        )

    async def test_validate__min_value(self):
        field = fields.Integer(default=10, min_value=11)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Integer(default=10, max_value=9)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['max_value'].format(
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
            fields.Float.errors['invalid']
        )

    async def test_validate__min_value(self):
        field = fields.Float(default=10.1, min_value=10.2)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Float(default=10.11, max_value=10.10)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['max_value'].format(
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
            fields.Choice.errors['invalid'].format(
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
            fields.Array.errors['invalid'].format(field)
        )

    async def test_validate__choices(self):
        field = fields.MultipleChoice(choices=self.choices.choices)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(['c'])

        self.assertEqual(
            context.exception.error,
            fields.MultipleChoice \
                .errors['choices'] \
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
            fields.Array.errors['invalid'].format(field)
        )

    async def test_validate__invalid_item(self):
        field = fields.Array(default=['j'], field=fields.Integer())

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Array.errors['child'].format(
                index=0,
                message=fields.Integer.errors['invalid']
            )
        )

    async def test_deserialize(self):
        field = fields.Array()

        self.assertEqual([], await field.deserialize([]))

    async def test_deserialize__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], await field.deserialize(['1']))

    async def test_serialize(self):
        field = fields.Array()

        self.assertEqual([1], field.serialize([1]))

    async def test_serialize__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], field.serialize([1]))


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
            fields.String.errors['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.URL(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.URL.errors['url']
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
            fields.String.errors['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.Host(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            fields.Host.errors['pattern'].format(field)
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
            fields.Map.errors['invalid'].format(field)
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
            fields.JSON.errors['invalid'].format(field)
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
            fields.Slug.errors['pattern'].format(field)
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

    async def test_serialize(self):
        field = fields.DateTime()

        self.assertEqual(
            '2015-07-13T00:00:00',
            field.serialize(datetime.datetime(2015, 7, 13))
        )

    async def test_deserialize(self):
        field = fields.DateTime()

        self.assertIsInstance(
            await field.deserialize('2015-07-13T14:08:12.000000'),
            datetime.datetime
        )

    async def test_to_db_value(self):
        field = fields.DateTime()
        datetime_ = datetime.datetime(2015, 7, 13)

        self.assertEqual(datetime_, await field.to_db_value(datetime_))

    async def test_deserialize__wrong_format(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.deserialize('wrong')

        self.assertEqual(
            context.exception.error,
            field.errors['invalid'].format(field)
        )

    async def test_deserialize__wrong_object(self):
        field = fields.DateTime()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.deserialize(object)

        self.assertEqual(
            context.exception.error,
            field.errors['invalid'].format(field)
        )


class DateTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.Date()

        self.assertEqual(
            '2015-07-13',
            field.serialize(datetime.date(2015, 7, 13))
        )

    async def test_deserialize(self):
        field = fields.Date()

        self.assertIsInstance(
            await field.deserialize('2015-07-13'), datetime.date
        )


class TimeTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.Time()

        self.assertEqual('00:00:00', field.serialize(datetime.time()))

    async def test_deserialize(self):
        field = fields.Time()

        self.assertIsInstance(
            await field.deserialize('14:08:12'), datetime.time
        )


class MethodTest(monstro.testing.AsyncTestCase):

    def test_serialize(self):
        value = datetime.datetime.now()

        self.assertEqual(value, fields.Method().serialize(value))
