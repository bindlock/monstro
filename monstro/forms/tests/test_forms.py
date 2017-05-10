import monstro.testing

from monstro import forms, db


class TestForm(forms.Form):

    string = forms.String(
        label='Label', help_text='Help', default='default', read_only=True
    )
    number = forms.Integer()


class TestModel(db.Model):

    string = db.String(default='default')
    number = db.Integer()

    class Meta:
        collection = 'test'


class TestModelForm(forms.ModelForm):

    float = db.Float()

    class Meta:
        model = TestModel
        fields = ('string',)


class FormTest(monstro.testing.AsyncTestCase):

    def test_new(self):
        self.assertIsInstance(TestForm.Meta.fields['string'], forms.String)
        self.assertIsInstance(TestForm.Meta.fields['number'], forms.Integer)

    async def test_validate(self):
        instance = TestForm(data={'number': '1'})

        await instance.validate()

        self.assertEqual(instance.data['number'], 1)

    async def test_validate__error(self):
        instance = TestForm(data={'string': 1})

        with self.assertRaises(forms.ValidationError) as context:
            await instance.validate()

        self.assertIn('string', context.exception.error)
        self.assertIn('string', instance.errors)

    async def test_get_options(self):
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
            }, (await TestForm.get_options())[0]
        )


class ModelFormTest(monstro.testing.AsyncTestCase):

    def test_new(self):
        self.assertEqual(
            TestModelForm.Meta.fields['string'],  # pylint:disable=E1126
            TestModel.Meta.fields['string']
        )

        self.assertNotIn('number', TestModelForm.Meta.fields)
        self.assertIsInstance(TestModelForm.Meta.fields['float'], db.Float)  # pylint:disable=E1126

    async def test_validate__read_only(self):
        TestModelForm.Meta.fields['string'].read_only = True  # pylint:disable=E1126
        instance = TestModelForm(data={'float': '1', 'string': 'value'})

        await instance.validate()

        self.assertEqual(
            instance.data['string'],
            TestForm.Meta.fields['string'].default
        )
