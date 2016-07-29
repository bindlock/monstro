# coding=utf-8

import unittest

import tornado.web

from .urls import include


class Handler(tornado.web.RequestHandler):

    pass


class IncludeTest(unittest.TestCase):

    def test(self):
        urls = [tornado.web.url('/test/', Handler)]

        url = include('/api/', urls)[0]

        self.assertEqual('/api/test/$', url.regex.pattern)

    def test__urls_as_string(self):
        with self.assertRaises(ImportError):
            include('/api/', 'urls')

    def test_namespace(self):
        urls = [tornado.web.url('/test/', Handler, name='test')]

        url = include('/api/', urls, namespace='api')[0]

        self.assertEqual('/api/test/$', url.regex.pattern)
        self.assertEqual('api:test', url.name)
