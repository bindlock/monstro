# coding=utf-8

import os
import importlib

import tornado.ioloop
from tornado.util import import_object

from monstro.forms import forms, fields
from monstro.core.exceptions import ImproperlyConfigured
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE


class SettingsSchema(forms.Form):

    secret_key = fields.String()
    debug = fields.Boolean()

    urls = fields.String()

    mongodb_uri = fields.String()
    mongodb_client_settings = fields.Map(required=False)

    tornado_application_settings = fields.Map(required=False)

    nosetests_arguments = fields.Array(required=False)


async def _import_settings_class():
    try:
        settings_path = os.environ[SETTINGS_ENVIRONMENT_VARIABLE]
    except KeyError:
        raise ImproperlyConfigured(
            'You must either define the environment variable "{}".'.format(
                SETTINGS_ENVIRONMENT_VARIABLE
            )
        )

    settings_class = import_object(settings_path)
    await SettingsSchema(instance=settings_class).validate()

    return settings_class


settings = tornado.ioloop.IOLoop.instance().run_sync(_import_settings_class)
