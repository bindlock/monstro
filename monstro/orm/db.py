# coding=utf-8

import os

import motor.motor_tornado

from monstro.conf import settings

from . import utils


db = None


def get_motor_connection(**kwargs):
    client = motor.motor_tornado.MotorClient(settings.mongodb_uri, **kwargs)
    return utils.MongoDBProxy(client)


def get_database(connection=None, database=None):
    if db and not (connection or database):
        return db

    database = database or os.environ.get('DB') or settings.mongodb_database

    global db  # pylint:disable=W0603
    connection = connection or get_motor_connection()
    db = connection[database]

    return db
