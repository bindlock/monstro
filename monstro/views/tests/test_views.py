# coding=utf-8

from unittest import mock
import urllib

import tornado.web

import monstro.testing
from monstro.forms import String
from monstro.orm import Model

from monstro.views import (
    View, ListView, TemplateView, DetailView, FormView, CreateView, UpdateView,
    RedirectView, DeleteView
)
from monstro.views.authentication import CookieAuthentication


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

    class TestSearchView(ListView):

        model = User
        template_name = 'index.html'
        search_fields = ('value',)

    def get_app(self):
        return tornado.web.Application([
            tornado.web.url(r'/', self.TestView),
            tornado.web.url(r'/search', self.TestSearchView),
        ])

    def test_get(self):
        with mock.patch.object(self.TestView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('test', response.body.decode('utf-8'))

    def test_get__search(self):
        with mock.patch.object(self.TestSearchView, 'render_string') as m:
            m.return_value = 'test'
            response = self.fetch('/search?q=1')

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
            self.run_sync(User.objects.get, value=user.value)
