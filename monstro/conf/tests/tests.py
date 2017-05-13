import os
import unittest.mock

from monstro.testing import AsyncTestCase
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE
from monstro.core.exceptions import ImproperlyConfigured
from monstro.conf import import_settings_class, default


class SettingsTest(AsyncTestCase):

    def setUp(self):
        super().setUp()

        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = (
            'monstro.conf.default.Settings'
        )

    async def test_import(self):
        settings = await import_settings_class()

        self.assertEqual(settings, default.Settings)

    async def test_import__invalid(self):
        with unittest.mock.patch('monstro.conf.default.Settings.urls', None):
            with self.assertRaises(ImproperlyConfigured):
                await import_settings_class()

    async def test_import__not_found(self):
        os.environ.pop(SETTINGS_ENVIRONMENT_VARIABLE)

        with self.assertRaises(ImproperlyConfigured):
            await import_settings_class()
