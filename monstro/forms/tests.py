# coding=utf-8

import unittest

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.utils import Choices

from . import fields, forms, exceptions, widgets


class FieldTest(monstro.testing.AsyncTestCase):

    def test_init(self):
        field = fields.Integer(default='1')

        self.assertEqual(field.default, '1')
        self.assertEqual(field.validators, [])

    def test_init__empty(self):
        field = fields.Integer()

        self.assertEqual(field.default, None)
        self.assertEqual(field.validators, [])

    @tornado.testing.gen_test
    def test__validation_error(self):
        field = fields.Integer()

        with self.assertRaises(exceptions.ValidationError):
            yield field.validate('a')

    @tornado.testing.gen_test
    def test__validation_error_required(self):
        field = fields.Integer(required=True)

        with self.assertRaises(exceptions.ValidationError):
            yield field.validate(None)

    @tornado.testing.gen_test
    def test__validation__validators(self):

        @tornado.gen.coroutine
        def validator(value):
            raise exceptions.ValidationError(value)

        field = fields.Integer(validators=[validator])

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


class FormTest(monstro.testing.AsyncTestCase):

    def test_init__with_data(self):
        instance = forms.Form(data={'name': 'test'})

        self.assertEqual({}, instance.__values__)

    def test_init__with_instance(self):
        class CustomForm(forms.Form):

            name = fields.String()

        class Instance(object):

            name = 'test'

        instance = CustomForm(instance=Instance)

        self.assertEqual(instance.__values__['name'], 'test')

    def test_new(self):
        class CustomForm(forms.Form):

            name = fields.String()

        self.assertIn('name', CustomForm.__fields__)

    def test_set_value(self):
        class CustomForm(forms.Form):

            name = fields.String()

        instance = CustomForm(data={'name': ''})
        instance.name = 'test'

        self.assertEqual(instance.name, 'test')

    @tornado.testing.gen_test
    def test_getattr__attribute_error(self):
        class CustomForm(forms.Form):

            name = fields.String()

        instance = CustomForm(data={'name': 'test'})

        with self.assertRaises(AttributeError):
            instance.none()

    @tornado.testing.gen_test
    def test_construct(self):
        class CustomForm(forms.Form):

            map = fields.Map()

        instance = CustomForm(data={'map': '{"name": "test"}'})

        yield instance.construct()

        self.assertEqual(instance.map['name'], 'test')

    @tornado.testing.gen_test
    def test_validate(self):
        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String()

        instance = CustomForm(data={'string': 'test'})

        data = yield instance.validate()

        self.assertEqual(data['string'], 'test')

    @tornado.testing.gen_test
    def test_validate__error(self):
        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String()

        instance = CustomForm(data={'string': 1})

        with self.assertRaises(exceptions.ValidationError) as context:
            yield instance.validate()

        self.assertIn('string', context.exception.error)

    @tornado.testing.gen_test
    def test__read_only(self):

        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String(read_only=True)

        instance = CustomForm(data={'string': '1'})

        with self.assertRaises(exceptions.ValidationError) as context:
            yield instance.validate()

        self.assertEqual(
            instance.__fields__['string'].error_messages['read_only'],
            context.exception.error['string']
        )

    @tornado.testing.gen_test
    def test_get_metadata(self):
        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String(
                label='Label', help_text='Help', default='default'
            )

        instance = CustomForm(data={'string': 1})

        self.assertEqual([{
            'name': 'string',
            'label': 'Label',
            'help_text': 'Help',
            'required': True,
            'read_only': False,
            'default': 'default',
            'widget': {
                'attrs': {'type': 'text'},
                'tag': 'input',
            }
        }], (yield instance.get_metadata()))

    @tornado.testing.gen_test
    def test_serialize(self):
        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String(
                label='Label', help_text='Help', default='default'
            )

        instance = CustomForm(data={'string': '1'})

        self.assertEqual({'string': '1'}, (yield instance.serialize()))

    @tornado.testing.gen_test
    def test_save(self):
        class CustomForm(forms.Form):
            __collection__ = 'test'

            string = fields.String(
                label='Label', help_text='Help', default='default'
            )

        CustomForm(data={'string': '1'}).save()


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
    def test_to_internal_value__invalid(self):
        field = fields.Array()

        self.assertEqual(None, (yield field.to_internal_value('wrong')))

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
    def test_to_internal_value__invalid_json(self):
        field = fields.Map()

        self.assertEqual(None, (yield field.to_internal_value('wrong')))

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


class WidgetTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.Widget('test', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'test',
            'attrs': {'key': 'value'},
        }, widget.get_metadata())


class InputTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.Input('hidden', attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'input',
            'attrs': {'key': 'value', 'type': 'hidden'},
        }, widget.get_metadata())


class TextAreaTest(unittest.TestCase):

    def test_get_metadata(self):
        widget = widgets.TextArea(attributes={'key': 'value'})

        self.assertEqual({
            'tag': 'textarea',
            'attrs': {'key': 'value'},
        }, widget.get_metadata())


class SelectTest(unittest.TestCase):

    def test_get_metadata(self):
        choice = Choices(
            ('A', 'a', 'A'),
            ('B', 'b', 'B')
        )
        widget = widgets.Select(
            choices=choice.choices, attributes={'key': 'value'}
        )

        self.assertEqual({
            'tag': 'select',
            'attrs': {'key': 'value'},
            'options': [
                {'label': 'A', 'value': 'a'},
                {'label': 'B', 'value': 'b'}
            ],
        }, widget.get_metadata())
