import asyncio

import tornado.ioloop
import tornado.testing

from monstro.db import databases


__all__ = (
    'AsyncTestCase',
    'AsyncHTTPTestCase'
)


class AsyncTestCaseMixin(object):

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

    async def tearDown(self):
        database = databases.get()
        await database.client.drop_database(database.name)

    def async_method_wrapper(self, function):
        def wrapper(*args, **kwargs):
            ioloop = self.get_new_ioloop()

            return ioloop.run_sync(lambda: function(*args, **kwargs))

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
