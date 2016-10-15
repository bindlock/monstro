# coding=utf-8

import uuid

from bson.objectid import ObjectId

import monstro.testing
from monstro.forms import fields
from monstro.forms.exceptions import ValidationError

from monstro.orm import model
from monstro.orm.fields import ForeignKey, Id, ManyToMany


class TestModel(model.Model):

    __collection__ = uuid.uuid4().hex

    name = fields.String()

monstro.testing.TestModel = TestModel


class IdTest(monstro.testing.AsyncTestCase):

    async def test_to_python(self):
        field = Id()

        value = await field.to_python(str(ObjectId()))

        self.assertIsInstance(value, ObjectId)

    async def test_validate(self):
        field = Id(default=ObjectId())

        await field.validate()

    async def test_to_python__wrong_object(self):
        field = Id()

        with self.assertRaises(ValidationError) as context:
            await field.to_python(object)

        self.assertEqual(
            context.exception.error, Id.error_messages['invalid']
        )

    async def test_validate__error(self):
        field = Id(default='blackjack')

        with self.assertRaises(ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error, Id.error_messages['invalid']
        )


class ForeignKeyTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test
        self.instance = await self.model.objects.create(name=uuid.uuid4().hex)

    def test_init__with_related_model_as_string(self):
        field = ForeignKey(to='monstro.testing.TestModel')

        self.assertEqual(TestModel, field.get_related_model())

    def test_init__with_related_model_as_string__self(self):
        field = ForeignKey(to='self')
        field.bind(model=TestModel)

        self.assertEqual(TestModel, field.get_related_model())

    async def test_validate__with_related_model_as_string(self):
        field = ForeignKey(to='self')
        field.bind(model=TestModel)

        instance = await TestModel.objects.create(name=uuid.uuid4().hex)

        await field.validate(instance._id)

    async def test_to_python(self):
        field = ForeignKey(to=self.model, to_field='name')
        value = await field.to_python(self.instance.name)

        self.assertEqual(value.name, self.instance.name)

    async def test_to_python__from_instance(self):
        field = ForeignKey(to=self.model, to_field='name')
        value = await field.to_python(self.instance)

        self.assertEqual(value.name, self.instance.name)

    async def test_to_python__from_not_saved_instance(self):
        field = ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.to_python(self.model())

        self.assertEqual(
            context.exception.error,
            ForeignKey.error_messages['foreign_key']
        )

    async def test_to_python__from_string_id(self):
        field = ForeignKey(to=self.model)
        value = await field.to_python(self.instance._id)

        self.assertEqual(value.name, self.instance.name)

    async def test_validate(self):
        field = ForeignKey(
            default=self.instance, to=self.model,
            to_field='name'
        )
        await field.validate()

        self.assertIsInstance(self.instance, self.model)

    async def test_to_internal_value__id(self):
        field = ForeignKey(to=self.model)

        value = await field.to_internal_value(self.instance)

        self.assertEqual(str(self.instance._id), value)

    async def test_validate__from_key(self):
        field = ForeignKey(to=self.model, to_field='name')
        await field.validate(self.instance.name)

        self.assertIsInstance(self.instance, self.model)

    async def test_validate__error(self):
        field = ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.validate('blackjack')

        self.assertEqual(
            context.exception.error,
            ForeignKey.error_messages['foreign_key']
        )

    async def test_validate__error_wrong_model(self):
        field = ForeignKey(to=self.model, to_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.validate(fields.String())

        self.assertEqual(
            context.exception.error,
            ForeignKey.error_messages['invalid'].format(field)
        )

    async def test_get_options(self):
        for __ in range(3):
            await self.model.objects.create(name='test')

        field = ForeignKey(to=self.model, to_field='name')

        self.assertEqual(
            4, len((await field.get_options())['widget']['options'])
        )

    async def test_get_options__with_to_python(self):

        class Model(model.Model):

            __collection__ = '__models__'

            foreign = ForeignKey(to=self.model)

            def __str__(self):
                return self.foreign.name

        name = 'test'
        instance = await self.model.objects.create(name=name)
        await Model.objects.create(foreign=instance)

        field = ForeignKey(to=Model)

        self.assertEqual(
            name, (await field.get_options())['widget']['options'][0]['label']
        )


class ManyToManyTest(monstro.testing.AsyncTestCase):

    async def setUp(self):
        super().setUp()

        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

            def __str__(self):
                return self.name

        self.model = Test

    async def test_validate(self):
        field = ManyToMany(to=self.model)
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(instances, await field.validate(instances))

    async def test_to_internal_value(self):
        field = ManyToMany(to=self.model, to_field='name')
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(
            [instance.name for instance in instances],
            await field.to_internal_value(instances)
        )

    async def test_get_options(self):
        field = ManyToMany(to=self.model)
        instances = [
            await self.model.objects.create(name=uuid.uuid4().hex),
            await self.model.objects.create(name=uuid.uuid4().hex)
        ]

        self.assertEqual(
            [{'value': str(i._id), 'label': i.name} for i in instances],
            (await field.get_options())['widget']['options']
        )
