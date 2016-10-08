# coding=utf-8

import uuid

from bson.objectid import ObjectId

import monstro.testing
from monstro.forms import fields
from monstro.forms.exceptions import ValidationError

from monstro.orm import model
from monstro.orm.fields import ForeignKey, Id


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
            context.exception.error, Id.default_error_messages['invalid']
        )

    async def test_validate__error(self):
        field = Id(default='blackjack')

        with self.assertRaises(ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error, Id.default_error_messages['invalid']
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
        field = ForeignKey(related_model='monstro.testing.TestModel')

        self.assertEqual(TestModel, field.get_related_model())

    def test_init__with_related_model_as_string__self(self):
        field = ForeignKey(related_model='self')
        field.bind(model=TestModel)

        self.assertEqual(TestModel, field.get_related_model())

    async def test_validate__with_related_model_as_string(self):
        field = ForeignKey(related_model='self')
        field.bind(model=TestModel)

        instance = await TestModel.objects.create(name=uuid.uuid4().hex)

        await field.validate(instance._id)

    async def test_to_python(self):
        field = ForeignKey(related_model=self.model, related_field='name')
        value = await field.to_python(self.instance.name)

        self.assertEqual(value.name, self.instance.name)

    async def test_to_python__from_instance(self):
        field = ForeignKey(related_model=self.model, related_field='name')
        value = await field.to_python(self.instance)

        self.assertEqual(value.name, self.instance.name)

    async def test_to_python__from_not_saved_instance(self):
        field = ForeignKey(related_model=self.model, related_field='name')

        with self.assertRaises(ValidationError) as context:
            await field.to_python(self.model())

        self.assertEqual(
            context.exception.error,
            ForeignKey.default_error_messages['foreign_key']
        )

    async def test_to_python__from_string_id(self):
        field = ForeignKey(related_model=self.model)
        value = await field.to_python(self.instance._id)

        self.assertEqual(value.name, self.instance.name)

    async def test_validate(self):
        field = ForeignKey(
            default=self.instance, related_model=self.model,
            related_field='name'
        )
        await field.validate()

        self.assertIsInstance(self.instance, self.model)

    async def test_to_internal_value__id(self):
        field = ForeignKey(related_model=self.model)

        value = await field.to_internal_value(self.instance)

        self.assertEqual(str(self.instance._id), value)

    async def test_validate__from_key(self):
        field = ForeignKey(
            default=self.instance.name, related_model=self.model,
            related_field='name'
        )
        await field.validate()

        self.assertIsInstance(self.instance, self.model)

    async def test_validate__error(self):
        field = ForeignKey(
            default='blackjack', related_model=self.model, related_field='name'
        )

        with self.assertRaises(ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            ForeignKey.default_error_messages['foreign_key']
        )

    async def test_validate__error_wrong_model(self):
        field = ForeignKey(
            default=fields.String(),
            related_model=self.model, related_field='name'
        )

        with self.assertRaises(ValidationError) as context:
            await field.validate()

        self.assertEqual(
            context.exception.error,
            ForeignKey.default_error_messages['invalid'].format(field)
        )

    async def test_get_metadata(self):
        for __ in range(3):
            await self.model.objects.create(name='test')

        field = ForeignKey(
            related_model=self.model, related_field='name'
        )

        self.assertEqual(
            4, len((await field.get_metadata())['widget']['options'])
        )
