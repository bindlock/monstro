# coding=utf-8

import tornado.gen
import tornado.testing
import tornado.ioloop

from tornado.testing import gen_test

import monstro.conf
import monstro.orm.db
from monstro.core.constants import TEST_DATABASE


class AsyncTestCase(tornado.testing.AsyncTestCase):

    drop_database_on_finish = False
    drop_database_every_test = False

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

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
            yield monstro.orm.db.client.drop_database(TEST_DATABASE)

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(
                lambda: monstro.orm.db.client.drop_database(TEST_DATABASE)
            )


class AsyncHTTPTestCase(tornado.testing.AsyncHTTPTestCase):

    drop_database_on_finish = False
    drop_database_every_test = False

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

    def get_app(self):
        raise NotImplementedError()

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
            yield monstro.orm.db.client.drop_database(TEST_DATABASE)

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(
                lambda: monstro.orm.db.client.drop_database(TEST_DATABASE)
            )

        super().tearDownClass()
