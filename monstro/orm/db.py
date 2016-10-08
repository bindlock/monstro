# coding=utf-8

import os

import motor.motor_tornado

from monstro.conf import settings
from monstro.core.constants import MONGODB_URI_ENVIRONMENT_VARIABLE

from . import proxy


def get_client(**kwargs):
    client_settings = getattr(settings, 'mongodb_client_settings', {}).copy()
    client_settings.update(kwargs)

    motor_client = motor.motor_tornado.MotorClient(
        os.environ.get(MONGODB_URI_ENVIRONMENT_VARIABLE, settings.mongodb_uri),
        **client_settings
    )

    return proxy.MotorProxy(motor_client)


client = get_client()
database = proxy.MotorProxy(client.get_default_database())
