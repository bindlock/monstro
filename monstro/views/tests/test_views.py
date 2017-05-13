from unittest import mock
import urllib

import tornado.web

from monstro import forms, db
from monstro.views import (
    View, ListView, TemplateView, DetailView, FormView,
    CreateView, UpdateView, RedirectView, DeleteView
)
from monstro.views.authenticators import CookieAuthenticator
import monstro.testing


class User(db.Model):

    value = db.String()

    class Meta:
        collection = 'users'


class UserForm(forms.ModelForm):

    value = forms.String()

    class Meta:
        model = User


class RedirectViewTest(monstro.testing.AsyncHTTPTestCase):

    def get_app(self):

        class TestView(RedirectView):

            redirect_url = '/r'

        return tornado.web.Application([tornado.web.url(r'/', TestView)])

    def test_get(self):
        response = self.fetch('/', follow_redirects=False)

        self.assertEqual(301, response.code)


class ViewTest(monstro.testing.AsyncHTTPTestCase):

    class TestView(View):

        authenticators = (CookieAuthenticator(User, 'value'),)

        async def get(self):
            self.write(self.request.method)

        @View.authenticated('/')
        async def options(self):
            self.write(self.request.method)

        @View.authenticated('http://github.com')
        async def head(self):
            self.write(self.request.method)

    def get_app(self):
        return tornado.web.Application(
            [tornado.web.url(r'/', self.TestView)],
            cookie_secret='test'
        )

    def test_get(self):
        response = self.fetch('/')

        self.assertEqual(200, response.code)
        self.assertEqual('GET', response.body.decode('utf-8'))

    def test_get_auth(self):
        user = self.run_sync(User.objects.create, value='test')

        with mock.patch.object(self.TestView, 'get_secure_cookie') as m:
            m.return_value = user.value.encode()
            response = self.fetch('/', method='OPTIONS')

        self.assertEqual(200, response.code)
        self.assertEqual('OPTIONS', response.body.decode('utf-8'))

    def test_get_auth__error(self):
        response = self.fetch('/', method='OPTIONS', follow_redirects=False)

        self.assertEqual(302, response.code)

    def test_get_auth__error__absolute_url(self):
        response = self.fetch('/', method='HEAD', follow_redirects=False)

        self.assertEqual(302, response.code)


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

    class TestView(FormView):

        form_class = UserForm
        template_name = 'index.html'
        redirect_url = '/'

        async def form_valid(self, form):
            await form.save()
            return await super().form_valid(form)

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

    class TestView(UpdateView):  # pylint:disable=R0901

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
            '/{}'.format(user.value),
            method='DELETE',
            follow_redirects=False
        )

        self.assertEqual(301, response.code)

        with self.assertRaises(User.DoesNotExist):
            self.run_sync(User.objects.get, value=user.value)
