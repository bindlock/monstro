# coding=utf-8

import argparse

import tornado.ioloop
import tornado.httpserver

from monstro.core.app import application
from monstro.conf import settings
import monstro.orm.db


def execute(args):
    argparser = argparse.ArgumentParser(description='Run Monstro server')

    argparser.add_argument('--host', default='127.0.0.1')
    argparser.add_argument('--port', default=8000)

    args = argparser.parse_args(args)

    server = tornado.httpserver.HTTPServer(application)
    server.bind(address=args.host, port=args.port)

    if settings.debug:
        server.start()
    else:
        server.start(getattr(settings, 'tornado_processes', None))

    print('Listen on {0.host}:{0.port}'.format(args))

    io_loop = tornado.ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()

    connection = monstro.orm.db.get_motor_connection(io_loop=io_loop)
    monstro.orm.db.db = monstro.orm.db.get_database(connection)
