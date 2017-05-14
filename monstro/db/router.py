import os

import motor

from monstro.conf import settings
from monstro.core.constants import TEST_ENVIRONMENT_VARIABLE

from . import proxy


class Router(object):

    def __init__(self):
        test = TEST_ENVIRONMENT_VARIABLE in os.environ

        self.__databases = {}

        for database in settings.databases:
            client = proxy.MotorProxy(
                motor.MotorClient(
                    database['uri'],
                    **database.get('options')
                )
            )

            name = database['name']

            if test:
                name = 'test_{}'.format(name)

            self.set(database['alias'], client[name])

    def get(self, alias='default'):
        return self.__databases[alias]

    def set(self, alias, database):
        assert isinstance(database, (motor.MotorDatabase, proxy.MotorProxy))

        if isinstance(database, motor.MotorDatabase):
            database = proxy.MotorProxy(database)

        self.__databases[alias] = database


databases = Router()
