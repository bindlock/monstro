# coding=utf-8

import unittest

import tornado.web

from monstro.urls.resolver import Resolver


class ResolverTest(unittest.TestCase):

    def test(self):
        pattern = (r'^/login/$', object, {'k': 'v'}, 'login')
        resolver = Resolver((pattern,))
        url = resolver.resolve()[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.regex.pattern, pattern[0])
        self.assertEqual(url.handler_class, pattern[1])
        self.assertEqual(url.kwargs, pattern[2])
        self.assertEqual(url.name, pattern[3])

    def test__dict_pattern(self):
        pattern = {
            'pattern': r'^/login/$', 'handler': object,
            'kwargs': {'k': 'v'}, 'name': 'login'
        }
        resolver = Resolver((pattern,))
        url = resolver.resolve()[0]

        self.assertIsInstance(url, tornado.web.url)
        self.assertEqual(url.regex.pattern, pattern['pattern'])
        self.assertEqual(url.handler_class, pattern['handler'])
        self.assertEqual(url.kwargs, pattern['kwargs'])
        self.assertEqual(url.name, pattern['name'])
