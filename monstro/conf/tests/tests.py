# coding=utf-8

import os

from monstro.testing import AsyncTestCase
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE
from monstro.core.exceptions import ImproperlyConfigured
from monstro.conf import _import_settings_class, default


class SettingsTest(AsyncTestCase):

    def setUp(self):
        super().setUp()

        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = (
            'monstro.conf.default.Settings'
        )

    async def test_import(self):
        settings = await _import_settings_class()

        self.assertEqual(settings, default.Settings)

    async def test_import__error(self):
        os.environ.pop(SETTINGS_ENVIRONMENT_VARIABLE)

        with self.assertRaises(ImproperlyConfigured):
            await _import_settings_class()
