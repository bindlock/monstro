# coding=utf-8

from unittest import mock
import urllib

import tornado.web
import tornado.gen

import monstro.testing
from monstro.forms import String
from monstro.orm import Model

from .views import (
    View, ListView, TemplateView, DetailView, FormView, CreateView, UpdateView,
    RedirectView, DeleteView
)
from .pagination import Pagination, PageNumberPagination, LimitOffsetPagination
from .authentication import (
    Authentication, HeaderAuthentication, CookieAuthentication
)

class User(Model):

    __collection__ = 'users'

    value = String()


class RedirectViewTest(monstro.testing.AsyncHTTPTestCase):

    def get_app(self):

        class TestView(RedirectView):

            redirect_url = '/r'

        return tornado.web.Application([tornado.web.url(r'/', TestView)])

    def test_get(self):
        response = self.fetch('/', follow_redirects=False)

        self.assertEqual(301, response.code)


class ViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestAuthView(View):

        authentication = CookieAuthentication(User, 'value')

        @tornado.web.authenticated
        def options(self):
            self.write(self.request.method)

    def get_app(self):

        class TestView(View):

            def get(self):
                self.write(self.request.method)

        return tornado.web.Application(
            [
                tornado.web.url(r'/', TestView),
                tornado.web.url(r'/auth', self.TestAuthView)
            ], cookie_secret='test', login_url='/'
        )

    def test_get(self):
        response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('GET', response.body.decode('utf-8'))

    def test_get_auth(self):
        user = self.run_sync(User.objects.create, value='test')
        with mock.patch.object(self.TestAuthView, 'get_secure_cookie') as m:
            m.return_value = user.value
            response = self.fetch('/auth', method='OPTIONS')

        self.assertEqual(200, response.code)
        self.assertEqual('OPTIONS', response.body.decode('utf-8'))

    def test_get_auth__error(self):
        response = self.fetch('/auth', method='OPTIONS')

        self.assertEqual(401, response.code)


class TemplateViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestView(TemplateView):

        template_name = 'index.html'

    def get_app(self):
        return tornado.web.Application([tornado.web.url(r'/', self.TestView)])

    def test_get(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))


class ListViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestView(ListView):

        model = User
        template_name = 'index.html'

    def get_app(self):
        return tornado.web.Application([tornado.web.url(r'/', self.TestView)])

    def test_get(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))


class DetailViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True

    class TestView(DetailView):

        model = User
        template_name = 'index.html'
        lookup_field = 'value'

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/(?P<value>\w+)', self.TestView)]
        )

    def test_get(self):
        user = self.run_sync(User.objects.create, value='test')

        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/{}'.format(user.value))

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))

    def test_get_404(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/wrong')

        self.assertEqual(404, response.code)


class FormViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True

    class TestView(FormView):

        form_class = User
        template_name = 'index.html'
        redirect_url = '/'

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/', self.TestView)]
        )

    def test_get(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))

    def test_post(self):
        data = {'value': 'test'}

        response = self.fetch(
            '/', method='POST', body=urllib.parse.urlencode(data),
            follow_redirects=False
        )

        self.assertEqual(302, response.code)

        self.run_sync(User.objects.get, **data)

    def test_post__invalid(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/', method='POST', body='')

        self.assertEqual(200, response.code)


class CreateViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True

    class TestView(CreateView):

        model = User
        template_name = 'index.html'
        redirect_url = '/'

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/', self.TestView)]
        )

    def test_get(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))

    def test_post(self):
        data = {'value': 'test'}

        response = self.fetch(
            '/', method='POST', body=urllib.parse.urlencode(data),
            follow_redirects=False
        )

        self.assertEqual(302, response.code)

        self.run_sync(User.objects.get, **data)


class UpdateViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True

    class TestView(UpdateView):

        model = User
        template_name = 'index.html'
        redirect_url = '/'
        lookup_field = 'value'

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/(?P<value>\w+)', self.TestView)]
        )

    def test_post(self):
        user = self.run_sync(User.objects.create, value='test')
        data = {'value': user.value[::-1]}

        response = self.fetch(
            '/{}'.format(user.value), method='POST',
            body=urllib.parse.urlencode(data), follow_redirects=False
        )

        self.assertEqual(302, response.code)
        self.assertEqual(user._id, self.run_sync(User.objects.get, **data)._id)


class DeleteViewTest(monstro.testing.AsyncHTTPTestCase):

    drop_database_on_finish = True

    class TestView(DeleteView):

        model = User
        redirect_url = '/'
        lookup_field = 'value'

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/(?P<value>\w+)', self.TestView)]
        )

    def test_delete(self):
        user = self.run_sync(User.objects.create, value='test')

        response = self.fetch(
            '/{}'.format(user.value), method='DELETE', follow_redirects=False
        )

        self.assertEqual(302, response.code)

        with self.assertRaises(User.DoesNotExist):
            user = self.run_sync(User.objects.get, value=user.value)
            print(user._id)


class PaginationTest(monstro.testing.AsyncTestCase):

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.bind()

    def test_get_offset__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.get_offset()

    def test_get_limit__not_implemented(self):
        pagination = Pagination()

        with self.assertRaises(NotImplementedError):
            pagination.get_limit()

    @tornado.testing.gen_test
    def test_serialize(self):
        pagination = Pagination()

        self.assertEqual(1, (yield pagination.serialize(1)))

    @tornado.testing.gen_test
    def test_serialize__serializer(self):
        pagination = Pagination(self.TestModel)
        instance = self.TestModel(data={'value': 'test'})

        self.assertEqual(
            {'value': 'test', '_id': None},
            (yield pagination.serialize(instance))
        )

    @tornado.testing.gen_test
    def test_serialize__other_serializer(self):
        pagination = Pagination(self.TestModel)
        instance = User(data={'value': 'test'})

        self.assertEqual(
            {'value': 'test', '_id': None},
            (yield pagination.serialize(instance))
        )


class PageNumberPaginationTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.page)
        self.assertEqual(1, pagination.count)

    def test_get_offset(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(0, pagination.get_offset())

    def test_get_limit(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        self.assertEqual(1, pagination.get_limit())

    @tornado.testing.gen_test
    def test_paginate(self):
        pagination = PageNumberPagination()
        pagination.bind(page=1, count=1)

        for i in range(5):
            yield self.TestModel.objects.create(value=str(i))

        data = yield pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(0, data['page'])
        self.assertEqual(5, data['count'])
        self.assertEqual(5, data['pages'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('0', data['items'][0].value)


class LimitOffsetPaginationTest(monstro.testing.AsyncTestCase):

    drop_database_on_finish = True

    class TestModel(Model):

        __collection__ = 'test'

        value = String()

    def test_bind(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(1, pagination.limit)
        self.assertEqual(2, pagination.offset)

    def test_get_offset(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(2, pagination.get_offset())

    def test_get_limit(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        self.assertEqual(3, pagination.get_limit())

    @tornado.testing.gen_test
    def test_paginate(self):
        pagination = LimitOffsetPagination()
        pagination.bind(limit=1, offset=2)

        for i in range(5):
            yield self.TestModel.objects.create(value=str(i))

        data = yield pagination.paginate(self.TestModel.objects.filter())

        self.assertEqual(2, data['page'])
        self.assertEqual(5, data['count'])
        self.assertEqual(5, data['pages'])
        self.assertEqual(1, len(data['items']))
        self.assertEqual('2', data['items'][0].value)


class AuthenticationTest(monstro.testing.AsyncTestCase):

    @tornado.testing.gen_test
    def test_get_credentials__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            yield Authentication().get_credentials(None)

    @tornado.testing.gen_test
    def test_authenticate__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            yield Authentication().authenticate(None)


class CookieAuthenticationTest(monstro.testing.AsyncTestCase):

    class User(Model):

        __collection__ = 'tokens'

        value = String()

    authentication = CookieAuthentication(User, 'value')

    @tornado.testing.gen_test
    def test_authenticate(self):
        user = yield self.User.objects.create(value='cookie')
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: user.value}
        )

        auth = yield self.authentication.authenticate(view)

        self.assertEqual(user._id, auth._id)

    @tornado.testing.gen_test
    def test_authenticate__error(self):
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: 'wrong'}
        )

        auth = yield self.authentication.authenticate(view)

        self.assertEqual(None, auth)


class HeaderAuthenticationTest(monstro.testing.AsyncTestCase):

    class Token(Model):

        __collection__ = 'tokens'

        value = String()

    authentication = HeaderAuthentication(Token, 'value')

    @tornado.testing.gen_test
    def test_authenticate(self):
        token = yield self.Token.objects.create(value='token')
        request = type(
            'Request', (object,), {'headers': {'Authorization': token.value}}
        )
        view = type('View', (object,), {'request': request})

        auth = yield self.authentication.authenticate(view)

        self.assertEqual(token._id, auth._id)

    @tornado.testing.gen_test
    def test_authenticate__error(self):
        request = type(
            'Request', (object,), {'headers': {'Authorization': 'wrong'}}
        )
        view = type('View', (object,), {'request': request})

        auth = yield self.authentication.authenticate(view)

        self.assertEqual(None, auth)
