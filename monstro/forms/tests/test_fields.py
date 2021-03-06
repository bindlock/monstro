import datetime
import re

import monstro.testing
from monstro.utils import Choices

from monstro.forms import fields, exceptions


class FieldTest(monstro.testing.AsyncTestCase):

    async def test_deserialize(self):
        field = fields.Field()

        self.assertEqual(None, await field.deserialize(None))

    async def test_serialize(self):
        field = fields.Field()

        self.assertEqual(None, await field.serialize(None))

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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.String.errors['min_length'].format(
                field
            )
        )

    async def test_validate__max_length(self):
        field = fields.String(max_length=3, default='test')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.String.errors['max_length'].format(
                field
            )
        )

    async def test_serialize__none(self):
        field = fields.String()

        self.assertEqual(None, await field.serialize(None))


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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Integer(default=10, max_value=9)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Numeric.errors['min_value'].format(
                field
            )
        )

    async def test_validate__max_value(self):
        field = fields.Float(default=10.11, max_value=10.10)

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

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
            await field.validate(None)

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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Array.errors['invalid'].format(field)
        )

    async def test_validate__invalid_item(self):
        field = fields.Array(default=['j'], field=fields.Integer())

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            {0: fields.Integer.errors['invalid']}
        )

    async def test_deserialize(self):
        field = fields.Array()

        self.assertEqual([], await field.deserialize([]))

    async def test_deserialize__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], await field.deserialize(['1']))

    async def test_serialize(self):
        field = fields.Array()

        self.assertEqual([1], await field.serialize([1]))

    async def test_serialize__with_field(self):
        field = fields.Array(field=fields.Integer())

        self.assertEqual([1], await field.serialize([1]))


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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.String.errors['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.URL(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.String.errors['invalid']
        )

    async def test_validate__invalid(self):
        field = fields.Host(default=':/wrong')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

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
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Map.errors['invalid'].format(field)
        )

    async def test_deserialize__schema(self):
        field = fields.Map(schema={'id': fields.Integer()})

        self.assertEqual(
            {'id': 1},
            await field.deserialize({'id': '1'})
        )

    async def test_deserialize__schema_error(self):
        field = fields.Map(schema={'id': fields.Integer()})

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.deserialize({'id': 'i'})

        self.assertEqual(
            {'id': fields.Integer.errors['invalid']},
            context.exception.error,
        )

    async def test_serialize__schema(self):
        field = fields.Map(schema={'dt': fields.DateTime()})
        dt = datetime.datetime.now()

        self.assertEqual(
            {'dt': dt.isoformat()},
            await field.serialize({'dt': dt})
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

    async def test_serialize(self):
        self.assertIsInstance(await fields.JSON().serialize({}), str)


class SlugTest(monstro.testing.AsyncTestCase):

    async def test_validate(self):
        field = fields.Slug()
        self.assertEqual(
            'back-jack-100_1', await field.validate('back-jack-100_1')
        )

    async def test_validate__error(self):
        field = fields.Slug(default='wrong slug')

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error,
            fields.Slug.errors['pattern'].format(field)
        )


class DateTimeTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.DateTime()

        self.assertEqual(
            '2015-07-13T00:00:00',
            await field.serialize(datetime.datetime(2015, 7, 13))
        )

    async def test_deserialize(self):
        field = fields.DateTime()

        self.assertIsInstance(
            await field.deserialize('2015-07-13T14:08:12.000000'),
            datetime.datetime
        )

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
            await field.serialize(datetime.date(2015, 7, 13))
        )

    async def test_deserialize(self):
        field = fields.Date()

        self.assertIsInstance(
            await field.deserialize('2015-07-13'), datetime.date
        )


class TimeTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.Time()

        self.assertEqual('00:00:00', await field.serialize(datetime.time()))

    async def test_deserialize(self):
        field = fields.Time()

        self.assertIsInstance(
            await field.deserialize('14:08:12'), datetime.time
        )


class PythonPathTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.PythonPath()

        self.assertEqual('monstro.forms.fields', await field.serialize(fields))

    async def test_serialize__class(self):
        field = fields.PythonPath()

        self.assertEqual(
            fields.PythonPath.__module__,
            await field.serialize(fields.PythonPath)
        )

    async def test_deserialize(self):
        field = fields.PythonPath()

        self.assertIs(await field.deserialize('monstro.forms.fields'), fields)

    async def test_deserialize__import_error(self):
        field = fields.PythonPath()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.deserialize('monstro.wrong')

        self.assertEqual(
            context.exception.error,
            field.errors['import'].format(field)
        )


class RegularExpressionTest(monstro.testing.AsyncTestCase):

    async def test_serialize(self):
        field = fields.RegularExpression()
        pattern = re.compile(r'\d+')

        self.assertEqual(pattern.pattern, await field.serialize(pattern))

    async def test_deserialize(self):
        field = fields.RegularExpression()
        pattern = re.compile(r'\d+')

        self.assertEqual(pattern, await field.deserialize(pattern.pattern))

    async def test_deserialize__error(self):
        field = fields.RegularExpression()

        with self.assertRaises(exceptions.ValidationError) as context:
            await field.deserialize('\\')

        self.assertEqual(
            context.exception.error,
            field.errors['invalid']
        )
