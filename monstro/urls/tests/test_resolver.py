import unittest

import tornado.web

from monstro.urls.resolver import Resolver, include


class ResolverTest(unittest.TestCase):

    def test(self):
        pattern = (r'^/login/$', object, {'k': 'v'}, 'login')
        resolver = Resolver((pattern,))
        url = list(resolver.resolve())[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.regex.pattern, pattern[0])
        self.assertEqual(url.handler_class, pattern[1])
        self.assertEqual(url.kwargs, pattern[2])
        self.assertEqual(url.name, pattern[3])

    def test__url_pattern(self):
        pattern = tornado.web.url(r'^/login/$', object)
        resolver = Resolver((pattern,))

        self.assertEqual(pattern, list(resolver.resolve())[0])

    def test__string_pattern(self):
        unittest.urls = (tornado.web.url(r'^/login/$', object),)
        resolver = Resolver('unittest.urls')

        self.assertEqual(unittest.urls[0], list(resolver.resolve())[0])

    def test__dict_pattern(self):
        pattern = {
            'pattern': r'^/login/$', 'handler': object,
            'kwargs': {'k': 'v'}, 'name': 'login'
        }
        resolver = Resolver((pattern,))
        url = list(resolver.resolve())[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.regex.pattern, pattern['pattern'])
        self.assertEqual(url.handler_class, pattern['handler'])
        self.assertEqual(url.kwargs, pattern['kwargs'])
        self.assertEqual(url.name, pattern['name'])

    def test__with_include(self):
        urls = ((r'^/login/$', object, {}, 'login'),)
        resolver = Resolver(((r'^/home/', include(urls, namespace='home')),))
        url = list(resolver.resolve())[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.matcher.regex.pattern, r'^/home/login/$')
        self.assertEqual(url.name, 'home:login')

    def test__with_resolver(self):
        urls = Resolver(((r'^/login/$', object, {}, 'login'),))
        resolver = Resolver((urls,))
        url = list(resolver.resolve())[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.matcher.regex.pattern, r'^/login/$')
        self.assertEqual(url.name, 'login')

    def test_iterable(self):
        pattern = tornado.web.url(r'^/login/$', object)
        resolver = Resolver((pattern,))

        for url in resolver:
            self.assertEqual(pattern, url)

    def test_reverse_url(self):
        urls = ((r'^/login/$', object, {}, 'login'),)
        resolver = Resolver(((r'^/home/', include(urls, namespace='home')),))
        application = tornado.web.Application(resolver)

        self.assertEqual('/home/login/', application.reverse_url('home:login'))

class IncludeTest(unittest.TestCase):

    def test(self):
        urls = ((r'^/login/$', object, {}, 'login'),)
        inclusion = include(urls)

        self.assertIsInstance(inclusion, Resolver)
        self.assertEqual(urls, inclusion.patterns)
