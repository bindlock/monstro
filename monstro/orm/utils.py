# coding=utf-8

import motor

from .decorators import autoreconnect


class MotorProxy(object):

    objects = (
        motor.MotorCollection,
        motor.MotorDatabase,
        motor.MotorGridFS,
        motor.MotorGridIn,
        motor.MotorGridOut,
        motor.MotorBulkOperationBuilder
    )

    def __init__(self, instance):
        self.instance = instance

    def __getattr__(self, attribute):
        attribute = getattr(self.instance, attribute)

        if callable(attribute) and not isinstance(attribute, self.objects):
            return autoreconnect()(attribute)

        return self.__class__(attribute)

    def __getitem__(self, item):
        return self.__class__(self.instance[item])

    def __repr__(self):
        return repr(self.instance)

    def __str__(self):
        return str(self.instance)
