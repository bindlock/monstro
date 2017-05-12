import motor

from monstro.conf import settings

from . import proxy


class Router(object):

    def __init__(self):
        self.__databases = {}

        for database in settings.databases:
            client = proxy.MotorProxy(
                motor.MotorClient(
                    database['uri'],
                    **database.get('options')
                )
            )
            self.set(database['alias'], client[database['name']])

    def get(self, alias='default'):
        return self.__databases[alias]

    def set(self, alias, database):
        assert isinstance(database, (motor.MotorDatabase, proxy.MotorProxy))

        if isinstance(database, motor.MotorDatabase):
            database = proxy.MotorProxy(database)

        self.__databases[alias] = database


databases = Router()
