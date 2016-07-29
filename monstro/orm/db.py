# coding=utf-8

import motor.motor_tornado

from monstro.conf import settings


def get_motor_connection(**kwargs):
    return motor.motor_tornado.MotorClient(settings.mongodb_uri, **kwargs)


def get_database(database=None):
    return get_motor_connection()[database or settings.mongodb_database]
