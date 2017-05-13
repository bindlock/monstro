import datetime
import uuid

from monstro.forms.exceptions import ValidationError
from monstro.db import fields, model, manager, proxy, databases
import monstro.testing


class ModelTest(monstro.testing.AsyncTestCase):

    def test_str(self):
        instance = model.Model()

        self.assertTrue(str(instance))

    async def test_equal(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)
        instance_ = await CustomModel.objects.get(string=instance.string)

        self.assertEqual(instance, instance_)

    def test_new(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = CustomModel()

        self.assertIsInstance(CustomModel.Meta.collection, proxy.MotorProxy)
        self.assertEqual(CustomModel.objects.model, CustomModel)
        self.assertIn('string', instance.Meta.fields)
        self.assertIn('_id', instance.Meta.fields)

    def test_getattr__attribute_error(self):
        with self.assertRaises(AttributeError):
            model.Model().none()

    async def test_serialize(self):
        class CustomModel(model.Model):
            name = fields.String()
            dt = fields.DateTime()

            class Meta:
                collection = 'test'

        instance = CustomModel(name='test', dt=datetime.datetime.now())
        data = await instance.serialize()
        dt = data.pop('dt')

        self.assertEqual({'name': 'test', '_id': None}, data)
        self.assertIsInstance(dt, str)

    async def test_serialize__raw_fields(self):
        class CustomModel(model.Model):
            name = fields.String()
            dt = fields.DateTime()

            class Meta:
                collection = 'test'

        instance = CustomModel(name='test', dt=datetime.datetime.now())
        data = await instance.serialize(raw_fields=('dt',))
        dt = data.pop('dt')

        self.assertEqual({'name': 'test', '_id': None}, data)
        self.assertIsInstance(dt, datetime.datetime)

    async def test_db_serialize(self):
        class CustomModel(model.Model):
            string = fields.String(default='default')
            number = fields.Integer()

            class Meta:
                collection = 'test'

        instance = CustomModel(number=1)
        data = await instance.db_serialize()

        self.assertEqual(None, data['string'])
        self.assertEqual(instance.number, data['number'])

    async def test_save__force(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = CustomModel(string=None)
        await instance.save(force=True)

        self.assertEqual(None, instance.string)

    async def test_save__on_create(self):
        class CustomModel(model.Model):
            datetime = fields.DateTime(auto_now_on_create=True)

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)

        self.assertIsInstance(instance.datetime, datetime.datetime)

    async def test_update(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)

        await instance.update(string='test')

        self.assertEqual('test', instance.string)

    async def test_refresh(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)

        _instance = await CustomModel.objects.get(_id=instance._id)
        await _instance.update(string=uuid.uuid4().hex)

        self.assertEqual(instance._id, _instance._id)
        self.assertNotEqual(instance.string, _instance.string)

        await instance.refresh()

        self.assertEqual(instance.string, _instance.string)

    async def test_resave(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)

        instance.string = uuid.uuid4().hex
        await instance.save()

        _model = await instance.objects.get(string=instance.string)

        self.assertEqual(instance.string, _model.string)

    async def test_construct(self):
        class RelatedModel(model.Model):
            name = fields.String()

            class Meta:
                collection = 'test2'

        class CustomModel(model.Model):
            string = fields.String()
            related = fields.ForeignKey(to=RelatedModel, to_field='name')

            class Meta:
                collection = 'test'

        related_model = await RelatedModel.objects.create(
            name=uuid.uuid4().hex
        )

        instance = await CustomModel.objects.create(
            string=uuid.uuid4().hex, related=related_model
        )

        instance = await instance.objects.get(string=instance.string)

        self.assertEqual(related_model.name, instance.related.name)

    async def test_validate(self):
        class FirstModel(model.Model):
            name = fields.String()

            class Meta:
                collection = 'test2'

        class SecondModel(model.Model):
            name = fields.String()
            related = fields.ForeignKey(to=FirstModel)

            class Meta:
                collection = 'test'

        class ThirdModel(model.Model):
            name = fields.String()
            related = fields.ForeignKey(to=SecondModel)

            class Meta:
                collection = 'test3'

        first = await FirstModel.objects.create(name=uuid.uuid4().hex)
        second = await SecondModel.objects.create(
            name=uuid.uuid4().hex, related=first
        )
        third = await ThirdModel.objects.create(
            name=uuid.uuid4().hex, related=second
        )

        self.assertIsInstance(second.related, FirstModel)
        self.assertIsInstance(third.related, SecondModel)
        self.assertIsInstance(third.related.related, FirstModel)

        second.related = 'wrong'

        with self.assertRaises(ValidationError) as context:
            await second.save()

        self.assertIn('related', context.exception.error)

    async def test_validate__unique(self):

        class CustomModel(model.Model):
            key = fields.String(unique=True)

            class Meta:
                collection = uuid.uuid4().hex

        await CustomModel.prepare()
        instance = await CustomModel.objects.create(key=uuid.uuid4().hex)

        with self.assertRaises(ValidationError) as context:
            await CustomModel.objects.create(key=instance.key)

        self.assertEqual(
            context.exception.error['key'],
            CustomModel.Meta.errors['unique']
        )

    async def test_delete(self):
        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'

        instance = await CustomModel.objects.create(string=uuid.uuid4().hex)
        await instance.delete()

        with self.assertRaises(instance.DoesNotExist):
            await instance.objects.get(string=instance.string)

    async def test_custom_manager(self):
        class CustomManager(manager.Manager):

            async def create(self, **kwargs):
                return None

        class CustomModel(model.Model):
            string = fields.String()

            class Meta:
                collection = 'test'
                objects = CustomManager()

        instance = await CustomModel.objects.create()

        self.assertFalse(instance)

    async def test_prepare(self):
        class CustomModel(model.Model):
            key = fields.String(unique=True)

            class Meta:
                collection = uuid.uuid4().hex

        await CustomModel.prepare()

        indexes = await CustomModel.Meta.collection.index_information()

        self.assertEqual(2, len(indexes))

    async def test_using(self):
        class CustomModel(model.Model):
            key = fields.String()

            class Meta:
                collection = uuid.uuid4().hex

        databases.set('another', databases.get().instance)

        self.assertNotEqual(
            CustomModel.Meta.collection.name,
            CustomModel.using(collection=uuid.uuid4().hex).Meta.collection.name
        )

    async def test_deserialize__raw_fields(self):
        class CustomModel(model.Model):
            key = fields.Integer()

            class Meta:
                collection = uuid.uuid4().hex

        instance = CustomModel(key='1')
        await instance.deserialize(raw_fields=('key',))

        self.assertIsInstance(instance.key, str)

    async def test_get_options(self):
        class CustomModel(model.Model):
            key = fields.Integer(label='Label', help_text='Help')

            class Meta:
                collection = uuid.uuid4().hex

        self.assertEqual(
            {
                'name': 'key',
                'label': 'Label',
                'help_text': 'Help',
                'required': True,
                'read_only': False,
                'default': None,
                'widget': {
                    'attrs': {'type': 'text'},
                    'tag': 'input',
                }
            }, (await CustomModel.get_options())[1]
        )

    async def test_from_db(self):
        class CustomModel(model.Model):
            integer = fields.Integer()
            string = fields.String()

            class Meta:
                collection = uuid.uuid4().hex

        instance = await CustomModel.from_db({'integer': 'j', 'string': 'k'})

        self.assertIsInstance(instance.string, str)
        self.assertIs(instance.integer, None)
