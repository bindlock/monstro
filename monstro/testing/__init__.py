# coding=utf-8

import tornado.gen
import tornado.ioloop

from tornado.testing import gen_test  # shortcut for import

from monstro.orm import db


__all__ = (
    'AsyncTestCase',
    'AsyncHTTPTestCase',
    'gen_test'
)


class AsyncTestCaseMixin(object):

    drop_database_on_finish = False
    drop_database_every_test = False

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(lambda: db.client.drop_database(db.database.name))

        super().tearDownClass()


class AsyncTestCase(AsyncTestCaseMixin, tornado.testing.AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.setUpAsync()

    def tearDown(self):
        self.tearDownAsync()
        super().tearDown()

    @tornado.testing.gen_test
    def setUpAsync(self):
        pass

    @tornado.testing.gen_test
    def tearDownAsync(self):
        if self.drop_database_every_test:
            yield db.client.drop_database(db.database.name)


class AsyncHTTPTestCase(AsyncTestCaseMixin, tornado.testing.AsyncHTTPTestCase):

    def setUp(self):
        super().setUp()
        self.io_loop.run_sync(self.setUpAsync)

    def tearDown(self):
        self.io_loop.run_sync(self.tearDownAsync)
        super().tearDown()

    @tornado.gen.coroutine
    def setUpAsync(self):
        pass

    @tornado.gen.coroutine
    def tearDownAsync(self):
        if self.drop_database_every_test:
            yield db.client.drop_database(db.database.name)
