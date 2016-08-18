# coding=utf-8

import os
import importlib

from monstro.core.exceptions import ImproperlyConfigured
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE
from tornado.util import import_object
from monstro.modules import ModulesRegistry


def _import_settings_class():
    try:
        return import_object(os.environ[SETTINGS_ENVIRONMENT_VARIABLE])
    except KeyError:
        raise ImproperlyConfigured(
            'You must either define the environment variable {}'.format(
                SETTINGS_ENVIRONMENT_VARIABLE
            )
        )

settings = _import_settings_class()
modules = ModulesRegistry(settings.modules)
