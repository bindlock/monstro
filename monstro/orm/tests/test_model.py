# coding=utf-8

import uuid

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
