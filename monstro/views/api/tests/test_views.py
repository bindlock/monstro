import json

from tornado.httputil import url_concat
import tornado.web

from monstro import forms, db
from monstro.views.paginators import PageNumberPaginator
from monstro.views.authenticators import HeaderAuthenticator
import monstro.testing

from monstro.views.api import APIView, ModelAPIView


class APIViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestForm(forms.Form):

        value = forms.String()

        async def validate(self):
            await super().validate()

            if self.data['value'] == 'wrong':
                raise self.ValidationError('wrong')

    def get_app(self):

        class TestView(APIView):

            form_class = self.TestForm

            async def get(self):
                self.write({'key': 'value'})

            async def post(self):
                self.write({'key': 'value'})

            async def put(self):
                self.write(self.data)

            async def delete(self):
                self.write(self.request.GET)

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
                'details': {'message': 'Unable to parse JSON'},
                'status': 'error',
                'code': 400
            }, data
        )

    def test_post__validate(self):
        payload = {'value': 'wrong'}
        response = self.fetch('/', method='POST', body=json.dumps(payload))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual({'message': 'wrong'}, data['details'])

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

    class TestForm(forms.Form):

        value = forms.String()

    class Token(db.Model):

        value = db.String()

        class Meta:
            collection = 'tokens'

    def get_app(self):

        class TestView(APIView):

            authenticators = (HeaderAuthenticator(self.Token, 'value'),)

            @APIView.authenticated
            async def get(self):
                self.write({'key': 'value'})

        return tornado.web.Application(
            [tornado.web.url(r'/', TestView, name='test')]
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
        self.assertEqual(401, data['code'])
        self.assertIn('Unauthorized', data['details']['message'])


class ModelAPIViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestModel(db.Model):

        value = db.String()

        class Meta:
            collection = 'test'

        async def validate(self):
            data = await super().validate()

            if self.value == 'wrong':
                raise self.ValidationError('wrong')

            return data

    def get_handler(self):

        class TestForm(forms.ModelForm):

            value = forms.String(required=False)

            class Meta:
                model = self.TestModel
                fields = ('value',)

        class TestView(ModelAPIView):  # pylint:disable=R0901

            model = self.TestModel
            form_class = TestForm

        return TestView

    def get_app(self):
        return tornado.web.Application([self.get_handler().get_url()])

    def test_reverse_url(self):
        self.assertEqual('/test/', self.get_app().reverse_url('test', ''))

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

        response = self.fetch('/test/{}'.format(instance._id))
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual({'value': instance.value}, data)

    def test_get_instance__invalid_id(self):
        response = self.fetch('/test/invalid')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(404, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(404, data['code'])

    def test_get_instance__not_found(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')
        url = '/test/{}'.format(instance._id)
        self.run_sync(instance.delete)

        response = self.fetch(url)
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(404, response.code)
        self.assertEqual('error', data['status'])
        self.assertEqual(404, data['code'])

    def test_options(self):
        response = self.fetch('/test/invalid', method='OPTIONS')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)

        self.assertEqual('_id', data['lookup_field'])
        self.assertIn('fields', data)

    def test_post(self):
        payload = {'value': 'test'}
        response = self.fetch(
            '/test/', method='POST', body=json.dumps(payload)
        )

        self.assertEqual(201, response.code)

        self.run_sync(self.TestModel.objects.get, **payload)

    def test_post__error(self):
        response = self.fetch('/test/', method='POST', body=json.dumps({}))

        self.assertEqual(400, response.code)

    def test_post__validate(self):
        payload = {'value': 'wrong'}
        response = self.fetch(
            '/test/', method='POST', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual({'message': 'wrong'}, data['details'])

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

    def test_put__validate(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        payload = {'value': 'wrong'}
        response = self.fetch(
            '/test/{}'.format(instance._id), method='PUT',
            body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(400, response.code)
        self.assertEqual({'message': 'wrong'}, data['details'])

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

    class TestModel(db.Model):

        value = db.String()

        class Meta:
            collection = 'test'

    def get_handler(self):

        class TestView(ModelAPIView):  # pylint:disable=R0901

            model = self.TestModel
            paginator = PageNumberPaginator()

        return TestView

    def get_app(self):
        return tornado.web.Application([self.get_handler().get_url()])

    def test_get(self):
        for __ in range(2):
            self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch('/test/?count=1')
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(200, response.code)
        self.assertEqual(1, len(data['items']))


class ModelAPIViewWithFormsTest(monstro.testing.AsyncHTTPTestCase):

    class TestModel(db.Model):

        value = db.String()

        class Meta:
            collection = 'test'

    def get_view(self):

        class TestView(ModelAPIView):  # pylint:disable=R0901

            model = self.TestModel

        return TestView

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/model/?(?P<_id>\w*)/?', self.get_view())]
        )

    def test_post(self):
        payload = {'value': 'value'}

        response = self.fetch(
            '/model/', method='POST', body=json.dumps(payload)
        )
        data = json.loads(response.body.decode('utf-8'))

        self.assertEqual(201, response.code)

        instance = self.run_sync(self.TestModel.objects.last)

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
        self.assertEqual(400, data['code'])
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
        self.assertEqual(400, data['code'])
        self.assertIn('value', data['details'])

    def test_delete(self):
        instance = self.run_sync(self.TestModel.objects.create, value='test')

        response = self.fetch(
            '/model/{}/'.format(instance._id), method='DELETE'
        )

        self.assertEqual(200, response.code)

        with self.assertRaises(self.TestModel.DoesNotExist):
            self.run_sync(self.TestModel.objects.get, _id=instance._id)
