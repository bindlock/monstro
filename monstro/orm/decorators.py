# coding=utf-8

import logging

import pymongo


logger = logging.getLogger('monstro')


def autoreconnect(retries=None):

    def decorator(f):

        def wrapper(*args, **kwargs):
            count = 0

            while True:
                try:
                    return f(*args, **kwargs)
                except pymongo.errors.AutoReconnect:
                    logger.warning('#{} reconnect to MongoDB.'.format(count))
                    count += 1

                    if retries is not None and count >= retries:
                        raise

        return wrapper

    return decorator
