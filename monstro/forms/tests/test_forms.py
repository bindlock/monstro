# coding=utf-8

import monstro.testing

from monstro.forms import fields, forms, exceptions


class TestForm(forms.Form):

    __collection__ = 'test'

    string = fields.String(
        label='Label', help_text='Help', default='default', read_only=True
    )
    number = fields.Integer()


class FormTest(monstro.testing.AsyncTestCase):

    def test_init__with_data(self):
        instance = TestForm(data={'name': 'test'})

        self.assertEqual(
            {'string': 'default', 'number': None}, instance.__values__
        )

    def test_class_name(self):
        self.assertEqual('TestForm', TestForm.__name__)

    def test_init__with_instance(self):
        instance = TestForm(instance=type('Object', (object,), {'number': 1}))

        self.assertEqual(instance.__values__['number'], 1)

    def test_new(self):
        self.assertIsInstance(TestForm.__fields__['string'], fields.String)
        self.assertIsInstance(TestForm.__fields__['number'], fields.Integer)

    def test_set_value(self):
        instance = TestForm()
        instance.string = 'test'

        self.assertEqual(instance.string, 'test')

    def test_getattr__attribute_error(self):
        with self.assertRaises(AttributeError):
            TestForm().none()

    async def test_validate(self):
        instance = TestForm(data={'number': '1'})

        await instance.validate()

        self.assertEqual(instance.number, 1)

    async def test_validate__raw_fields(self):
        instance = TestForm(data={'number': '1'}, raw_fields=['number'])

        await instance.validate()

        self.assertEqual('1', instance.number)

    async def test_validate__error(self):
        instance = TestForm(data={'string': 1})

        with self.assertRaises(exceptions.ValidationError) as context:
            await instance.validate()

        self.assertIn('string', context.exception.error)
        self.assertIn('string', instance.__errors__)

    async def test_get_options(self):
        instance = TestForm()

        self.assertEqual(
            {
                'name': 'string',
                'label': 'Label',
                'help_text': 'Help',
                'required': False,
                'read_only': True,
                'default': 'default',
                'widget': {
                    'attrs': {'type': 'text'},
                    'tag': 'input',
                }
            }, (await instance.get_options())[0]
        )

    async def test_serialize(self):
        instance = await TestForm(data={'number': '1'}).deserialize()

        self.assertEqual(
            {'number': 1, 'string': 'default'}, (await instance.serialize())
        )

    async def test_serialize__raw_fields(self):
        instance = TestForm(data={'number': None}, raw_fields=['number'])

        self.assertEqual(
            {'number': None, 'string': 'default'}, (await instance.serialize())
        )

    async def test_deserialize(self):
        instance = await TestForm(data={'number': '1'}).deserialize()

        self.assertEqual(1, instance.number)

    async def test_deserialize__raw_fields(self):
        instance = TestForm(data={'number': '1'}, raw_fields=['number'])
        await instance.deserialize()

        self.assertEqual('1', instance.number)

    async def test_deserialize__wrong_value(self):
        instance = await TestForm(data={'number': 'wrong'}).deserialize()

        self.assertEqual(None, instance.number)

    async def test__read_only(self):
        instance = TestForm(data={'string': '1'})

        with self.assertRaises(exceptions.ValidationError) as context:
            await instance.validate()

        self.assertEqual(
            instance.__fields__['string'].errors['read_only'],
            context.exception.error['string']
        )
