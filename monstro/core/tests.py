# coding=utf-8

import monstro.testing

from .app import application


class APIHandlerTest(monstro.testing.AsyncHTTPTestCase):

    def get_app(self):
        return application

    def test(self):
        self.fetch('/')
