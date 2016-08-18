# coding=utf-8

import json

import tornado.web
import tornado.gen
from tornado.httputil import url_concat

import monstro.testing
from monstro.forms import Form, String, Integer
from monstro.orm import Model
from monstro.views.pagination import PageNumberPagination
from monstro.views.authentication import HeaderAuthentication

from .views import APIView, ModelAPIView


class APIViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestForm(Form):

        value = String()

    def get_app(self):

        class TestView(APIView):

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
            [tornado.web.url(r'/', TestView, name='test')]
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

    def test_delete(self):
        payload = {'value': 'test'}
        response = self.fetch(url_concat('/', payload), method='DELETE')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(payload, data)


class APIViewWithAuthenticationTest(monstro.testing.AsyncHTTPTestCase):

    class TestForm(Form):

        value = String()

    class Token(Model):

        __collection__ = 'tokens'

        value = String()

    def get_app(self):

        class TestView(APIView):

            authentication = HeaderAuthentication(self.Token, 'value')

            @tornado.gen.coroutine
            def get(self):
                self.write({'key': 'value'})

        return tornado.web.Application(
            [tornado.web.url(r'/', TestView, name='test')],
            login_url='/'
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
        print(response.body)
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(401, response.code)

        self.assertEqual('error', data['status'])
        self.assertEqual(401, data['status_code'])
        self.assertIn(
            'Authentication failed', data['details']['request_error']
        )


class ModelAPIViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    class TestForm(Form):

        value = String(required=False)

    def get_handler(self):
        class TestView(ModelAPIView):

            model = self.TestModel
            form_class = self.TestForm

        return TestView

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
        self.assertEqual([{'value': instance.value}], data['items'])

    def test_get_instance(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/{}/'.format(instance._id))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual({'value': instance.value}, data)

    def test_get_instance__invalid_id(self):
        response = self.fetch('/test/invalid/')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(404, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(404, data['status_code'])
        self.assertEqual('Object not found', data['details']['request_error'])

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
        self.assertIn('fields', data)

    def test_post(self):
        payload = {'value': 'test'}
        response = self.fetch('/test', method='POST', body=json.dumps(payload))

        self.assertEqual(201, response.code)

        self.run_sync(self.TestModel.objects.get, **payload)

    def test_post__error(self):
        payload = {}
        response = self.fetch('/test', method='POST', body=json.dumps(payload))

        self.assertEqual(400, response.code)

    def test_put(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        payload = {'value': instance.value[::-1]}
        response = self.fetch(
            '/test/{}'.format(instance._id), method='PUT',
            body=json.dumps(payload)
        )

        self.assertEqual(200, response.code)

        self.assertEqual(
            instance._id,
            self.run_sync(self.TestModel.objects.get, **payload)._id
        )

    def test_put__error(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        payload = {'value': None}
        response = self.fetch(
            '/test/{}'.format(instance._id), method='PUT',
            body=json.dumps(payload)
        )

        self.assertEqual(400, response.code)

    def test_patch(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        payload = {'value': instance.value[::-1]}
        response = self.fetch(
            '/test/{}'.format(instance._id), method='PATCH',
            body=json.dumps(payload)
        )

        self.assertEqual(200, response.code)

        self.assertEqual(
            instance._id,
            self.run_sync(self.TestModel.objects.get, **payload)._id
        )


class ModelAPIViewWithPaginatorTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def get_handler(self):

        class ModelForm(Form):

            _id = String()
            value = String()

        class TestView(ModelAPIView):

            forms = {
                'GET': {'model': ModelForm},
            }

            model = self.TestModel
            paginator = PageNumberPagination(
                self.TestModel.objects.filter(), ModelForm
            )

        return TestView

    def get_app(self):
        return tornado.web.Application([self.get_handler().get_url_spec()])

    def test_get(self):
        for __ in range(2):
            self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/?count=1')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(1, len(data['items']))


class ModelAPIViewWithFormsTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True
    drop_database_every_test = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def get_handler(self):

        class POSTForm(Form):

            value = String(required=False)

        class PATCHForm(Form):

            value = Integer()

        class TestView(ModelAPIView):

            model = self.TestModel
            forms = {
                'POST': {'body': POSTForm},
                'PATCH': {'body': PATCHForm}
            }

        return TestView

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/model/?(?P<_id>\w*)/?', self.get_handler())]
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
        print(data)

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
