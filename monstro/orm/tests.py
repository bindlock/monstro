# coding=utf-8

import uuid
import random

import tornado.gen
import tornado.testing
import tornado.ioloop

from bson.objectid import ObjectId

import monstro.testing
from monstro.forms import fields
from monstro.forms.exceptions import ValidationError

from . import model, queryset, manager, db
from .fields import ForeignKey, Id


class TestModel(model.Model):

    __collection__ = uuid.uuid4().hex

    name = fields.String()

monstro.testing.TestModel = TestModel


class GetDatabaseTest(monstro.testing.AsyncTestCase):

    def test_get_database(self):
        database = db.get_database()

        self.assertEqual(database, db.get_database())


class ModelTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    def test_init(self):
        instance = model.Model(data={})

        self.assertEqual({'_id': None}, instance.__values__)
        self.assertEqual(None, instance.__cursor__)
        self.assertFalse(hasattr(instance, 'objects'))

    def test_str(self):
        instance = model.Model(data={})

        self.assertTrue(str(instance))

    def test_new(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            name = fields.String()

        instance = CustomModel(data={})

        self.assertEqual('test', CustomModel.__collection__)
        self.assertEqual(CustomModel.objects.model, CustomModel)
        self.assertIn('name', instance.__fields__)
        self.assertIn('_id', instance.__fields__)

    def test_new_init_with__id_field(self):
        with self.assertRaises(AttributeError):

            class Test(model.Model):
                __collection__ = 'test'
                _id = fields.Integer()

    @tornado.testing.gen_test
    def test_getattr__attribute_error(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            name = fields.String()

        instance = CustomModel(data={'name': 'test'})

        with self.assertRaises(AttributeError):
            instance.none()

    @tornado.testing.gen_test
    def test_to_internal_value(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            name = fields.String()

        instance = CustomModel(data={'name': 'test'})

        self.assertEqual(
            {'name': 'test', '_id': None}, (yield instance.to_internal_value())
        )

    @tornado.testing.gen_test
    def test_save(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        _model = yield instance.objects.get(string=instance.string)

        self.assertEqual(instance.string, _model.string)

    @tornado.testing.gen_test
    def test_update(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        yield instance.update(string='test')

        self.assertEqual('test', instance.string)

    @tornado.testing.gen_test
    def test_refresh(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        _instance = yield instance.objects.get(_id=instance._id)
        yield _instance.update(string=uuid.uuid4().hex)

        self.assertEqual(instance._id, _instance._id)
        self.assertNotEqual(instance.string, _instance.string)

        yield instance.refresh()

        self.assertEqual(instance.string, _instance.string)

    @tornado.testing.gen_test
    def test_resave(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        instance.string = uuid.uuid4().hex
        yield instance.save()

        _model = yield instance.objects.get(string=instance.string)

        self.assertEqual(instance.string, _model.string)

    @tornado.testing.gen_test
    def test_construct(self):
        class RelatedModel(model.Model):
            __collection__ = 'test2'

            name = fields.String()

        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()
            related = ForeignKey(
                related_model=RelatedModel, related_field='name'
            )

        related_model = yield RelatedModel.objects.create(
            name=uuid.uuid4().hex
        )

        instance = yield CustomModel.objects.create(
            string=uuid.uuid4().hex, related=related_model
        )

        instance = yield instance.objects.get(string=instance.string)

        self.assertEqual(related_model.name, instance.related.name)

    @tornado.testing.gen_test
    def test_validate(self):
        class RelatedModel(model.Model):
            __collection__ = 'test2'

            name = fields.String()

        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()
            related = ForeignKey(
                related_model=RelatedModel, related_field='name'
            )

        related_model = RelatedModel(data={'name': uuid.uuid4().hex})
        yield related_model.save()

        instance = CustomModel(
            data={'string': uuid.uuid4().hex, 'related': related_model}
        )
        instance.related = 'wrong'

        with self.assertRaises(ValidationError):
            yield instance.save()

        try:
            yield instance.save()
        except ValidationError as e:
            self.assertIn('related', e.error)

    @tornado.testing.gen_test
    def test_validate__unique(self):

        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String(unique=True)

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        with self.assertRaises(ValidationError) as context:
            yield CustomModel.objects.create(string=instance.string)

        self.assertEqual(
            context.exception.error['string'],
            fields.Field.default_error_messages['unique']
        )

    @tornado.testing.gen_test
    def test_delete(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            string = fields.String()

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)
        yield instance.delete()

        with self.assertRaises(instance.DoesNotExist):
            yield instance.objects.get(string=instance.string)

    @tornado.testing.gen_test
    def test_custom_manager(self):
        class CustomManager(manager.Manager):

            @tornado.gen.coroutine
            def create(self, **kwargs):
                raise tornado.gen.Return(None)

        class CustomModel(model.Model):
            __collection__ = 'test'
            objects = CustomManager()

            string = fields.String()

        instance = yield CustomModel.objects.create()

        self.assertFalse(instance)


class ManagerTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test

        self.number = random.randint(10, 20)

        for i in range(self.number):
            yield self.model.objects.create(name='test{}'.format(i))

    @tornado.testing.gen_test
    def test_filter(self):
        count = yield self.model.objects.filter().count()

        self.assertEqual(self.number, count)

    @tornado.testing.gen_test
    def test_filter_with_query(self):
        count = yield self.model.objects.filter(name='test10').count()

        self.assertEqual(1, count)

    @tornado.testing.gen_test
    def test_create(self):
        instance = yield self.model.objects.create(name='New')
        count = yield self.model.objects.filter(name=instance.name).count()

        self.assertEqual(1, count)


class QuerySetTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def setUpAsync(self):
        class Test(model.Model):

            __collection__ = uuid.uuid4().hex

            name = fields.String()

        self.model = Test
        self.queryset = queryset.QuerySet(self.model)

        self.number = random.randint(10, 20)

        for i in range(self.number):
            yield self.model.objects.create(name='test{}'.format(i))

    def test_init(self):
        self.assertEqual(self.model, self.queryset.model)

    @tornado.testing.gen_test
    def test_filter(self):
        count = yield self.queryset.filter().count()

        self.assertEqual(self.number, count)

    @tornado.testing.gen_test
    def test_first_last(self):
        first = yield self.queryset.filter().first()
        last = yield self.queryset.filter().last()

        self.assertTrue(first.name < last.name)

    @tornado.testing.gen_test
    def test_filter_with_query(self):
        count = yield self.queryset.filter(name='test0').count()

        self.assertEqual(1, count)

    @tornado.testing.gen_test
    def test_all(self):
        items = yield self.queryset.filter().all()

        self.assertEqual(self.number, len(items))

    @tornado.testing.gen_test
    def test_slice(self):
        items = yield self.queryset.filter()[1:7]

        self.assertEqual(6, len(items))

    @tornado.testing.gen_test
    def test_slice_by_items(self):
        yield self.queryset.filter().all()
        items = yield self.queryset[1:7]

        self.assertEqual(6, len(items))

    @tornado.testing.gen_test
    def test_slice_left(self):
        number = random.randint(5, 7)

        items = yield (yield self.queryset.filter()[number:]).all()

        self.assertEqual(self.number - number, len(items))

    @tornado.testing.gen_test
    def test_slice_right(self):
        number = random.randint(5, 7)

        items = yield (yield self.queryset.filter()[:number]).all()

        self.assertEqual(number, len(items))

    @tornado.testing.gen_test
    def test_slice_index(self):
        number = random.randint(5, 7)

        instance = yield self.queryset.filter()[number]

        self.assertEqual('test{}'.format(number), instance.name)


class IdTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_to_representation(self):
        field = Id()

        value = yield field.to_representation(str(ObjectId()))

        self.assertIsInstance(value, ObjectId)

    @tornado.testing.gen_test
    def test_validate(self):
        field = Id(default=ObjectId())

        yield field.validate()

    @tornado.testing.gen_test
    def test_is_valid__from_string(self):
        field = Id()

        yield field.is_valid(str(ObjectId()))

    @tornado.testing.gen_test
    def test_is_valid__from_string_error(self):
        field = Id()

        with self.assertRaises(ValidationError) as context:
            yield field.is_valid('blackjack')

        self.assertEqual(
            context.exception.error,
            Id.default_error_messages['invalid']
        )

    @tornado.testing.gen_test
    def test_to_internal_value__from_string_error(self):
        field = Id()

        self.assertEqual(None, (yield field.to_internal_value('wrong')))

    @tornado.testing.gen_test
    def test_validate__error(self):
        field = Id(default='blackjack')

        with self.assertRaises(ValidationError) as context:
            yield field.validate()

        self.assertEqual(
            context.exception.error,
            Id.default_error_messages['invalid']
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
        field = ForeignKey(related_model='monstro.orm.tests.TestModel')

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
    def test_to_representation(self):
        field = ForeignKey(
            default=self.instance.name, related_model=self.model,
            related_field='name'
        )
        value = yield field.to_representation(field.default)

        self.assertEqual(value.name, self.instance.name)

    @tornado.testing.gen_test
    def test_to_representation__from_string_id(self):
        field = ForeignKey(related_model=self.model)
        value = yield field.to_representation(str(self.instance._id))

        self.assertEqual(value.name, self.instance.name)

    @tornado.testing.gen_test
    def test_to_representation__from_string_id_error(self):
        field = ForeignKey(related_model=self.model)

        self.assertEqual(None, (yield field.to_representation('blackjack')))

    @tornado.testing.gen_test
    def test_to_representation__does_not_exist(self):
        field = ForeignKey(related_model=self.model, related_field='name')

        self.assertEqual(None, (yield field.to_representation('blackjack')))

    @tornado.testing.gen_test
    def test_validate(self):
        field = ForeignKey(
            default=self.instance, related_model=self.model,
            related_field='name'
        )
        yield field.validate()

        self.assertIsInstance(self.instance, self.model)

    @tornado.testing.gen_test
    def test_is_valid(self):
        field = ForeignKey(
            related_model=self.model, related_field='name'
        )
        yield field.is_valid(self.instance)

        self.assertIsInstance(self.instance, self.model)

    @tornado.testing.gen_test
    def test_to_internal_value__id(self):
        field = ForeignKey(related_model=self.model)

        value = yield field.to_internal_value(self.instance)

        self.assertEqual(str(self.instance._id), value)

    @tornado.testing.gen_test
    def test_to_internal_value__invalid(self):
        field = ForeignKey(related_model=self.model)

        self.assertEqual(None, (yield field.to_internal_value(field)))

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
    def test_is_valid__error_wrong_model(self):
        field = ForeignKey(
            related_model=self.model, related_field='name'
        )

        with self.assertRaises(ValidationError) as context:
            yield field.is_valid(fields.String())

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
