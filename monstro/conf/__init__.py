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

    urls = forms.String()

    databases = forms.Array(
        field=forms.Map(schema={
            'alias': forms.String(default='default'),
            'uri': forms.String(),
            'name': forms.String(),
            'options': forms.Map(default={})
        })
    )

    tornado_application_settings = forms.Map(default={})

    nosetests_arguments = forms.Array(field=forms.String(), default=[])

    models = forms.Array(field=forms.String(), default=[])
    commands = forms.Map(default={})


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
    data = dict(settings_class.__dict__)

    for cls in reversed(settings_class.__mro__):
        data.update(cls.__dict__)

    try:
        await SettingsForm(data=data).validate()
    except SettingsForm.ValidationError as e:
        raise ImproperlyConfigured(e.error)

    return settings_class


settings = tornado.ioloop.IOLoop.instance().run_sync(import_settings_class)
