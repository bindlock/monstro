# coding=utf-8

import tornado.gen
import tornado.testing
import tornado.ioloop

from tornado.testing import gen_test

import monstro.conf
import monstro.orm.db


MONSTRO_TEST_DATABASE = '__monstro__'


class AsyncTestCase(tornado.testing.AsyncTestCase):

    drop_database_on_finish = False
    drop_database_every_test = False

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()

    def run_sync(self, function, *args, **kwargs):
        return self.io_loop.run_sync(lambda: function(*args, **kwargs))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        monstro.conf.settings.mongodb_database = MONSTRO_TEST_DATABASE

    def setUp(self):
        super().setUp()

        self.connection = monstro.orm.db.get_motor_connection(
            io_loop=self.io_loop
        )

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
            yield self.connection.drop_database(MONSTRO_TEST_DATABASE)

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            connection = monstro.orm.db.get_motor_connection()
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(
                lambda: connection.drop_database(MONSTRO_TEST_DATABASE)
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        monstro.conf.settings.mongodb_database = MONSTRO_TEST_DATABASE

    def setUp(self):
        super().setUp()

        self.connection = monstro.orm.db.get_motor_connection(
            io_loop=self.io_loop
        )

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
            yield self.connection.drop_database(MONSTRO_TEST_DATABASE)

    @classmethod
    def tearDownClass(cls):
        if cls.drop_database_on_finish:
            connection = monstro.orm.db.get_motor_connection()
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.run_sync(
                lambda: connection.drop_database(MONSTRO_TEST_DATABASE)
            )

        super().tearDownClass()
