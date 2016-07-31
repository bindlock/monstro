# coding=utf-8

import os
import importlib

import tornado.gen
import tornado.ioloop

from monstro.core.exceptions import ImproperlyConfigured
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE
from tornado.util import import_object
from monstro.modules import ModulesRegistry

from .schema import SettingsSchema


@tornado.gen.coroutine
def _import_settings_class():
    try:
        settings_class = import_object(
            os.environ[SETTINGS_ENVIRONMENT_VARIABLE]
        )
    except KeyError:
        raise ImproperlyConfigured(
            'You must either define the environment variable {}'.format(
                SETTINGS_ENVIRONMENT_VARIABLE
            )
        )

    try:
        yield SettingsSchema(instance=settings_class).validate()
    except SettingsSchema.ValidationError as e:
        raise ImproperlyConfigured(
            'Wrong settings. {}'.format(
                ' '.join(
                    '{} - {}.'.format(*pair) for pair in e.error.items()
                ).lower()
            )
        )

    return settings_class

io_loop = tornado.ioloop.IOLoop.current()
settings = io_loop.run_sync(_import_settings_class)

modules = ModulesRegistry(settings.modules)
