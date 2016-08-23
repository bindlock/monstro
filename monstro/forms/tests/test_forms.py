# coding=utf-8

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing

from monstro.forms import fields, forms, exceptions


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
