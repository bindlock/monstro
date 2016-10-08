# coding=utf-8

import asyncio

import tornado.ioloop
import tornado.testing

from monstro.orm import db


__all__ = (
    'AsyncTestCase',
    'AsyncHTTPTestCase'
)


class AsyncTestCaseMixin(object):

    drop_database_on_finish = False
    drop_database_every_test = False

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

    async def tearDown(self):
        if self.drop_database_every_test:
            await db.client.drop_database(db.database.name)

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(lambda: db.client.drop_database(db.database.name))

        super().tearDownClass()

    def async_method_wrapper(self, function):
        def wrapper(*args, **kwargs):
            return self.get_new_ioloop().run_sync(
                lambda: function(*args, **kwargs)
            )

        return wrapper

    def __getattribute__(self, item):
        attribute = object.__getattribute__(self, item)

        if asyncio.iscoroutinefunction(attribute):
            return self.async_method_wrapper(attribute)

        return attribute


class AsyncTestCase(AsyncTestCaseMixin, tornado.testing.AsyncTestCase):

    pass


class AsyncHTTPTestCase(AsyncTestCaseMixin, tornado.testing.AsyncHTTPTestCase):

    pass
