# coding=utf-8

import json

import tornado.web
import tornado.gen
from tornado.httputil import url_concat

import monstro.testing
from monstro.serializers import Serializer, StringField, IntegerField
from monstro.orm import Model

from .handlers import APIHandler, ModelAPIHandler
from .pagination import Pagination, PageNumberPagination, LimitOffsetPagination
from .authentication import Authentication, TokenAuthentication


class APIHandlerTest(monstro.testing.AsyncHTTPTestCase):

    class TestSerializer(Serializer):

        value = StringField()

    def get_app(self):

        class TestHandler(APIHandler):

            serializers = {
                'PUT': {
                    'body': self.TestSerializer
                },
                'DELETE': {
                    'query': self.TestSerializer
                }
            }

            @tornado.gen.coroutine
            def get(self):
                self.write({'key': 'value'})

            @tornado.gen.coroutine
            def post(self):
                self.write({'key': 'value'})

            @tornado.gen.coroutine
            def put(self):
                self.write(self.data)

            @tornado.gen.coroutine
            def delete(self):
                self.write(self.query)

        return tornado.web.Application(
            [tornado.web.url(r'/', TestHandler, name='test')]
        )

    def test_get(self):
        response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('{"key": "value"}', response.body.decode('utf-8'))

    def test_unsupported_method(self):
        response = self.fetch('/', method='OPTIONS')

        self.assertEqual(405, response.code)

    def test_post(self):
        response = self.fetch('/', method='POST', body='')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual({'key': 'value'}, data)

    def test_post__wrong_json(self):
        response = self.fetch('/', method='POST', body='a')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual(
            {
                'details': {'request_error': 'Unable to parse JSON'},
                'status': 'error',
                'status_code': 400
            }, data
        )

    def test_put(self):
        payload = {'value': 'test'}
        response = self.fetch('/', method='PUT', body=json.dumps(payload))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(payload, data)

    def test_put__validation_error(self):
        payload = {}
        response = self.fetch('/', method='PUT', body=json.dumps(payload))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)

        self.assertEqual('error', data['status'])
        self.assertEqual(400, data['status_code'])
        self.assertIn('value', data['details'])

    def test_delete(self):
        payload = {'value': 'test'}
        response = self.fetch(url_concat('/', payload), method='DELETE')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(payload, data)

    def test_delete__validation_error(self):
        payload = {}
        response = self.fetch(url_concat('/', payload), method='DELETE')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)

        self.assertEqual('error', data['status'])
        self.assertEqual(400, data['status_code'])
        self.assertIn('value', data['details'])


class APIHandlerWithAuthenticationTest(monstro.testing.AsyncHTTPTestCase):

    class TestSerializer(Serializer):

        value = StringField()

    class Token(Model):

        __collection__ = 'tokens'

        value = StringField()

    def get_app(self):

        class TestHandler(APIHandler):

            authentication = TokenAuthentication(self.Token, 'value')

            @tornado.gen.coroutine
            def get(self):
                self.write({'key': 'value'})

        return tornado.web.Application(
            [tornado.web.url(r'/', TestHandler, name='test')]
        )

    def test_get(self):
        token = self.run_sync(self.Token.objects.create, value='test')
        headers = {'Authorization': token.value}

        response = self.fetch('/', headers=headers)
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)

        self.assertEqual({'key': 'value'}, data)

    def test_get__error_authentication(self):
        response = self.fetch('/')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(401, response.code)

        self.assertEqual('error', data['status'])
        self.assertEqual(401, data['status_code'])
        self.assertIn(
            'Authentication failed', data['details']['request_error']
        )


class ModelAPIHandlerTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def get_handler(self):
        class TestHandler(ModelAPIHandler):

            model = self.TestModel

        return TestHandler

    def get_app(self):
        return tornado.web.Application([self.get_handler().get_url_spec()])

    def test_get__empty(self):
        response = self.fetch('/test/')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual([], data['items'])

    def test_get(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(
            [{'value': instance.value, '_id': str(instance._id)}],
            data['items']
        )

    def test_get_instance(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/{}/'.format(instance._id))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(
            {'value': instance.value, '_id': str(instance._id)}, data
        )

    def test_get_instance__invalid_id(self):
        response = self.fetch('/test/invalid/')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(400, data['status_code'])
        self.assertEqual('Invalid Id', data['details']['request_error'])

    def test_get_instance__not_found(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')
        url = '/test/{}/'.format(instance._id)
        self.run_sync(instance.delete)

        response = self.fetch(url)
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(404, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(404, data['status_code'])
        self.assertEqual('Object not found', data['details']['request_error'])

    def test_options(self):
        response = self.fetch('/test/invalid/', method='OPTIONS')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)

        self.assertEqual('_id', data['lookup_field'])
        self.assertIn('input', data)
        self.assertIn('output', data)


class ModelAPIHandlerWithPaginatorTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def get_handler(self):

        class ModelSerializer(Serializer):

            _id = StringField()
            value = StringField()

        class TestHandler(ModelAPIHandler):

            serializers = {
                'GET': {'model': ModelSerializer},
            }

            model = self.TestModel
            paginator = PageNumberPagination(
                self.TestModel.objects.filter(), ModelSerializer
            )

        return TestHandler

    def get_app(self):
        return tornado.web.Application([self.get_handler().get_url_spec()])

    def test_get(self):
        for __ in range(2):
            self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/?count=1')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(1, len(data['items']))


class ModelAPIHandlerWithSerializersTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def get_handler(self):

        class POSTSerializer(Serializer):

            value = StringField(required=False)

        class PATCHSerializer(Serializer):

            value = IntegerField()

        class TestHandler(ModelAPIHandler):

            model = self.TestModel
            serializers = {
                'POST': {'body': POSTSerializer},
                'PATCH': {'body': PATCHSerializer}
            }

        return TestHandler

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/model/?(\w*)/?', self.get_handler())]
        )

    def test_post(self):
        payload = {'value': 'value'}

        response = self.fetch(
            '/model/', method='POST', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        instance = self.run_sync(self.TestModel.objects.last)

        self.assertEqual(201, response.code)
        self.assertEqual(payload['value'], instance.value)
        self.assertEqual(
            {'value': payload['value'], '_id': str(instance._id)}, data
        )

    def test_post__error(self):
        payload = {}

        response = self.fetch(
            '/model/', method='POST', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(400, data['status_code'])
        self.assertIn('value', data['details'])

    def test_put(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')
        payload = {'value': 'value'}

        response = self.fetch(
            '/model/{}/'.format(instance._id),
            method='PUT', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        instance = self.run_sync(self.TestModel.objects.last)

        self.assertEqual(200, response.code)
        self.assertEqual(payload['value'], instance.value)
        self.assertEqual(
            {'value': payload['value'], '_id': str(instance._id)}, data
        )

    def test_patch__error(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')
        payload = {'value': 1}

        response = self.fetch(
            '/model/{}/'.format(instance._id),
            method='PATCH', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(400, data['status_code'])
        self.assertIn('value', data['details'])

    def test_delete(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch(
            '/model/{}/'.format(instance._id), method='DELETE'
        )

        self.assertEqual(200, response.code)

        with self.assertRaises(self.TestModel.DoesNotExist):
            self.run_sync(self.TestModel.objects.get, _id=instance._id)


class PaginationTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def test_bind__not_implemented(self):
        paginator = Pagination(self.TestModel.objects.filter(), self.TestModel)

        with self.assertRaises(NotImplementedError):
            paginator.bind()

    def test_get_offset__not_implemented(self):
        paginator = Pagination(self.TestModel.objects.filter(), self.TestModel)

        with self.assertRaises(NotImplementedError):
            paginator.get_offset()

    def test_get_limit__not_implemented(self):
        paginator = Pagination(self.TestModel.objects.filter(), self.TestModel)

        with self.assertRaises(NotImplementedError):
            paginator.get_limit()


class PageNumberPaginationTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def test_bind(self):
        paginator = PageNumberPagination(
            self.TestModel.objects.filter(), self.TestModel
        )

        paginator.bind(page=1, count=1)

        self.assertEqual(1, paginator.page)
        self.assertEqual(1, paginator.count)

    def test_get_offset(self):
        paginator = PageNumberPagination(
            self.TestModel.objects.filter(), self.TestModel
        )
        paginator.bind(page=1, count=1)

        self.assertEqual(0, paginator.get_offset())

    def test_get_limit(self):
        paginator = PageNumberPagination(
            self.TestModel.objects.filter(), self.TestModel
        )
        paginator.bind(page=1, count=1)

        self.assertEqual(1, paginator.get_limit())


class LimitOffsetPaginationTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        __collection__ = 'test'

        value = StringField()

    def test_bind(self):
        paginator = LimitOffsetPagination(
            self.TestModel.objects.filter(), self.TestModel
        )

        paginator.bind(limit=1, offset=2)

        self.assertEqual(1, paginator.limit)
        self.assertEqual(2, paginator.offset)

    def test_get_offset(self):
        paginator = LimitOffsetPagination(
            self.TestModel.objects.filter(), self.TestModel
        )
        paginator.bind(limit=1, offset=2)

        self.assertEqual(2, paginator.get_offset())

    def test_get_limit(self):
        paginator = LimitOffsetPagination(
            self.TestModel.objects.filter(), self.TestModel
        )
        paginator.bind(limit=1, offset=2)

        self.assertEqual(1, paginator.get_limit())


class AuthenticationTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_authenticate__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            yield Authentication().authenticate(None)


class TokenAuthenticationTest(monstro.testing.AsyncTestCase):

    class Token(Model):

        __collection__ = 'tokens'

        value = StringField()

    authentication = TokenAuthentication(Token, 'value')

    @tornado.testing.gen_test
    def test_authenticate(self):
        token = yield self.Token.objects.create(value='token')
        request = type(
            'Request', (object,), {'headers': {'Authorization': token.value}}
        )

        auth = yield self.authentication.authenticate(request)

        self.assertEqual(token._id, auth._id)

    @tornado.testing.gen_test
    def test_authenticate__error(self):
        request = type(
            'Request', (object,), {'headers': {'Authorization': 'wrong'}}
        )

        auth = yield self.authentication.authenticate(request)

        self.assertEqual(None, auth)
