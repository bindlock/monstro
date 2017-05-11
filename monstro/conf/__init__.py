import importlib
import os

from tornado.util import import_object
import tornado.ioloop

from monstro import forms
from monstro.core.exceptions import ImproperlyConfigured
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE


class SettingsForm(forms.Form):

    secret_key = forms.String()
    debug = forms.Boolean()

    urls = forms.PythonPath()

    mongodb_uri = forms.String()
    mongodb_client_settings = forms.Map(required=False)

    tornado_application_settings = forms.Map(required=False)

    nosetests_arguments = forms.Array(field=forms.String(), required=False)

    models = forms.Array(field=forms.String(), required=False)
    commands = forms.Map(required=False)


async def import_settings_class():
    try:
        path = os.environ[SETTINGS_ENVIRONMENT_VARIABLE]
    except KeyError:
        raise ImproperlyConfigured(
            'You must either define the environment variable "{}".'.format(
                SETTINGS_ENVIRONMENT_VARIABLE
            )
        )

    settings_class = import_object(path)
    await SettingsForm(data=dict(settings_class.__dict__)).validate()

    return settings_class


settings = tornado.ioloop.IOLoop.instance().run_sync(import_settings_class)
