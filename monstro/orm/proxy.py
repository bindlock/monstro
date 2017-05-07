import logging

import pymongo
import motor.motor_tornado


logger = logging.getLogger('monstro')


def autoreconnect(retries=None):

    def decorator(f):

        def wrapper(*args, **kwargs):
            count = 0

            while True:
                try:
                    return MotorProxy.wrap(f(*args, **kwargs))
                except pymongo.errors.AutoReconnect:
                    logger.warning('#{} reconnect to MongoDB.'.format(count))
                    count += 1

                    if retries is not None and count >= retries:
                        raise

        return wrapper

    return decorator


class MotorProxy(object):

    objects = (
        motor.MotorCollection,
        motor.MotorDatabase,
        motor.MotorGridFS,
        motor.MotorGridIn,
        motor.MotorGridOut,
        motor.MotorBulkOperationBuilder,
        motor.motor_tornado.MotorCursor
    )

    def __init__(self, instance):
        self.instance = instance

    @classmethod
    def wrap(cls, object):  # pylint: disable=W0622
        if isinstance(object, cls.objects):
            return cls(object)
        elif callable(object):
            return autoreconnect()(object)

        return object

    def __getattr__(self, attribute):
        return self.wrap(getattr(self.instance, attribute))

    def __getitem__(self, item):
        return self.wrap(self.instance[item])

    def __repr__(self):
        return 'MotorProxy({})'.format(repr(self.instance))

    def __str__(self):
        return 'MotorProxy({})'.format(str(self.instance))
