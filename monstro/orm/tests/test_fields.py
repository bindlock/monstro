# coding=utf-8

import uuid

import tornado.gen
import tornado.testing
import tornado.ioloop

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

    @tornado.testing.gen_test
    def test_to_python(self):
        field = Id()

        value = yield field.to_python(str(ObjectId()))

        self.assertIsInstance(value, ObjectId)

    @tornado.testing.gen_test
    def test_validate(self):
        field = Id(default=ObjectId())

        yield field.validate()

    @tornado.testing.gen_test
    def test_to_python__wrong_object(self):
        field = Id()

        with self.assertRaises(ValidationError) as context:
            self.assertEqual('wrong', (yield field.to_python(object)))

        self.assertEqual(
            context.exception.error, Id.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_validate__error(self):
        field = Id(default='blackjack')

        with self.assertRaises(ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error, Id.default_error_messages['invalid']
        )


class ForeignKeyTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test
        self.instance = yield self.model.objects.create(name=uuid.uuid4().hex)

    @tornado.testing.gen_test
    def test_init__with_related_model_as_string(self):
        field = ForeignKey(related_model='monstro.testing.TestModel')

        self.assertEqual(TestModel, field.get_related_model())

    @tornado.testing.gen_test
    def test_init__with_related_model_as_string__self(self):
        field = ForeignKey(related_model='self')
        field.bind(model=TestModel)

        self.assertEqual(TestModel, field.get_related_model())

    @tornado.testing.gen_test
    def test_validate__with_related_model_as_string(self):
        field = ForeignKey(related_model='self')
        field.bind(model=TestModel)

        instance = yield TestModel.objects.create(name=uuid.uuid4().hex)

        yield field.validate(instance._id)

    @tornado.testing.gen_test
    def test_to_python(self):
        field = ForeignKey(
            default=self.instance.name, related_model=self.model,
            related_field='name'
        )
        value = yield field.to_python(field.default)

        self.assertEqual(value.name, self.instance.name)

    @tornado.testing.gen_test
    def test_to_python__from_string_id(self):
        field = ForeignKey(related_model=self.model)
        value = yield field.to_python(self.instance._id)

        self.assertEqual(value.name, self.instance.name)

    @tornado.testing.gen_test
    def test_validate(self):
        field = ForeignKey(
            default=self.instance, related_model=self.model,
            related_field='name'
        )
        yield field.validate()

        self.assertIsInstance(self.instance, self.model)

    @tornado.testing.gen_test
    def test_to_internal_value__id(self):
        field = ForeignKey(related_model=self.model)

        value = yield field.to_internal_value(self.instance)

        self.assertEqual(str(self.instance._id), value)

    @tornado.testing.gen_test
    def test_validate__from_key(self):
        field = ForeignKey(
            default=self.instance.name, related_model=self.model,
            related_field='name'
        )
        yield field.validate()

        self.assertIsInstance(self.instance, self.model)

    @tornado.testing.gen_test
    def test_validate__error(self):
        field = ForeignKey(
            default='blackjack', related_model=self.model, related_field='name'
        )

        with self.assertRaises(ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            ForeignKey.default_error_messages['foreign_key']
        )

    @tornado.testing.gen_test
    def test_validate__error_wrong_model(self):
        field = ForeignKey(
            default=fields.String(),
            related_model=self.model, related_field='name'
        )

        with self.assertRaises(ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            ForeignKey.default_error_messages['invalid'].format(field)
        )

    @tornado.testing.gen_test
    def test_get_metadata(self):
        for __ in range(3):
            yield self.model.objects.create(name='test')

        field = ForeignKey(
            related_model=self.model, related_field='name'
        )

        self.assertEqual(
            4, len((yield field.get_metadata())['widget']['options'])
        )
