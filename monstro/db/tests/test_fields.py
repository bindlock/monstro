import datetime
import uuid

from bson.objectid import ObjectId

from monstro.forms.exceptions import ValidationError
from monstro.db import fields, model
import monstro.testing


class TestModel(model.Model):
    name = fields.String()

    class Meta:
        collection = uuid.uuid4().hex

monstro.testing.TestModel = TestModel


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

    async def test_db_serialize(self):
        field = fields.DateTime()
        dt = datetime.datetime(2015, 7, 13)

        self.assertEqual(dt, await field.db_serialize(dt))


class IdTest(monstro.testing.AsyncTestCase):

    async def test_deserialize(self):
        field = fields.Id()

        value = await field.deserialize(str(ObjectId()))

        self.assertIsInstance(value, ObjectId)

    async def test_validate(self):
        field = fields.Id(default=ObjectId())

        await field.validate(None)

    async def test_deserialize__wrong_object(self):
        field = fields.Id()

        with self.assertRaises(ValidationError) as context:
            await field.deserialize(object)

        self.assertEqual(
            context.exception.error, fields.Id.errors['invalid']
        )

    async def test_validate__error(self):
        field = fields.Id(default='blackjack')

        with self.assertRaises(ValidationError) as context:
            await field.validate(None)

        self.assertEqual(
            context.exception.error, fields.Id.errors['invalid']
        )


class ForeignKeyTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):
            name = fields.String()

            class Meta:
                collection = uuid.uuid4().hex

        self.model = Test
        self.instance = await self.model.objects.create(name=uuid.uuid4().hex)

    def test_init__with_related_model_as_string(self):
        field = fields.ForeignKey(to='monstro.testing.TestModel')

        self.assertEqual(TestModel, field.get_related_model())

    def test_init__with_related_model_as_string__self(self):
        field = fields.ForeignKey(to='self')
        field.bind(model=TestModel)

        self.assertEqual(TestModel, field.get_related_model())

    async def test_validate__with_related_model_as_string(self):
        field = fields.ForeignKey(to='self')
        field.bind(model=TestModel)

        instance = await TestModel.objects.create(name=uuid.uuid4().hex)

        await field.validate(instance._id)

    async def test_deserialize(self):
        field = fields.ForeignKey(to=self.model, to_field='name')
        value = await field.deserialize(self.instance.name)

        self.assertEqual(value.name, self.instance.name)

    async def test_deserialize__from_instance(self):
        field = fields.ForeignKey(to=self.model, to_field='name')
        value = await field.deserialize(self.instance)

        self.assertEqual(value.name, self.instance.name)

    async def test_deserialize__from_not_saved_instance(self):
        field = fields.ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.deserialize(self.model())

        self.assertEqual(
            context.exception.error,
            fields.ForeignKey.errors['foreign_key']
        )

    async def test_deserialize__from_string_id(self):
        field = fields.ForeignKey(to=self.model)
        value = await field.deserialize(self.instance._id)

        self.assertEqual(value.name, self.instance.name)

    async def test_validate(self):
        field = fields.ForeignKey(
            default=self.instance, to=self.model,
            to_field='name'
        )
        await field.validate(None)

        self.assertIsInstance(self.instance, self.model)

    async def test_serialize__id(self):
        field = fields.ForeignKey(to=self.model)

        value = await field.serialize(self.instance)

        self.assertEqual(str(self.instance._id), value)

    async def test_validate__from_key(self):
        field = fields.ForeignKey(to=self.model, to_field='name')
        await field.validate(self.instance.name)

        self.assertIsInstance(self.instance, self.model)

    async def test_validate__error(self):
        field = fields.ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            fields.ForeignKey.errors['foreign_key']
        )

    async def test_validate__error_wrong_model(self):
        field = fields.ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.validate(fields.String())

        self.assertEqual(
            context.exception.error,
            fields.ForeignKey.errors['invalid'].format(field)
        )

    async def test_get_options(self):
        for __ in range(3):
            await self.model.objects.create(name='test')

        field = fields.ForeignKey(to=self.model, to_field='name')

        self.assertEqual(
            4, len((await field.get_options())['widget']['options'])
        )

    async def test_get_options__with_deserialize(self):

        class Model(model.Model):
            foreign = fields.ForeignKey(to=self.model)

            class Meta:
                collection = uuid.uuid4().hex

            def __str__(self):
                return self.foreign.name

        name = 'test'
        instance = await self.model.objects.create(name=name)
        await Model.objects.create(foreign=instance)

        field = fields.ForeignKey(to=Model)

        self.assertEqual(
            name, (await field.get_options())['widget']['options'][0]['label']
        )


class ManyToManyTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):
            name = fields.String()

            class Meta:
                collection = uuid.uuid4().hex

            def __str__(self):
                return self.name

        self.model = Test

    async def test_validate(self):
        field = fields.ManyToMany(to=self.model)
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(instances, await field.validate(instances))

    async def test_serialize(self):
        field = fields.ManyToMany(to=self.model, to_field='name')
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(
            [instance.name for instance in instances],
            await field.serialize(instances)
        )

    async def test_get_options(self):
        field = fields.ManyToMany(to=self.model)
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(
            [{'value': str(i._id), 'label': i.name} for i in instances],
            (await field.get_options())['widget']['options']
        )
