# coding=utf-8

import os

import tornado.testing

from monstro.testing import AsyncTestCase
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE
from monstro.core.exceptions import ImproperlyConfigured
from monstro.conf import _import_settings_class


class SettingsTest(AsyncTestCase):

    def setUp(self):
        super().setUp()

        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = (
            'monstro.conf.default.Settings'
        )

    @tornado.testing.gen_test
    def test_import(self):
        settings = _import_settings_class()

        self.assertTrue(settings.debug)

    @tornado.testing.gen_test
    def test_import__error(self):
        os.environ.pop(SETTINGS_ENVIRONMENT_VARIABLE)

        with self.assertRaises(ImproperlyConfigured):
            _import_settings_class()
