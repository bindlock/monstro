# coding=utf-8

import motor.motor_tornado

from monstro.conf import settings


db = None


def get_motor_connection(**kwargs):
    return motor.motor_tornado.MotorClient(settings.mongodb_uri, **kwargs)


def get_database(connection=None, database=None):
    if db and not (connection or database):
        return db

    global db
    connection = connection or get_motor_connection()
    db = connection[database or settings.mongodb_database]

    return db
