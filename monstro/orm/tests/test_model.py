# coding=utf-8

import uuid
import datetime

import tornado.gen
import tornado.testing
import tornado.ioloop

import monstro.testing
from monstro.forms import fields
from monstro.forms.exceptions import ValidationError

from monstro.orm import model, manager
from monstro.orm.fields import ForeignKey


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

            class Test(model.Model):  # pylint: disable=W0612
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
    def test_serialize(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            name = fields.String()

        instance = CustomModel(data={'name': 'test'})
        instance.__valid__ = True

        self.assertEqual(
            {'name': 'test', '_id': None}, (yield instance.serialize())
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
    def test_save__on_create(self):
        class CustomModel(model.Model):
            __collection__ = 'test'

            datetime = fields.DateTime(auto_now_on_create=True)

        instance = yield CustomModel.objects.create(string=uuid.uuid4().hex)

        self.assertIsInstance(instance.datetime, datetime.datetime)

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

        _instance = yield CustomModel.objects.get(_id=instance._id)
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
        class FirstModel(model.Model):
            __collection__ = 'test2'

            name = fields.String()

        class SecondModel(model.Model):
            __collection__ = 'test'

            name = fields.String()
            related = ForeignKey(related_model=FirstModel)

        class ThirdModel(model.Model):
            __collection__ = 'test'

            name = fields.String()
            related = ForeignKey(related_model=SecondModel)

        first = yield FirstModel.objects.create(name=uuid.uuid4().hex)
        second = yield SecondModel.objects.create(
            name=uuid.uuid4().hex, related=first
        )
        third = yield ThirdModel.objects.create(
            name=uuid.uuid4().hex, related=second
        )

        self.assertIsInstance(second.related, FirstModel)
        self.assertIsInstance(third.related, SecondModel)
        self.assertIsInstance(third.related.related, FirstModel)

        second.related = 'wrong'

        with self.assertRaises(ValidationError) as context:
            yield second.save()

        self.assertIn('related', context.exception.error)

        try:
            yield second.save()
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
