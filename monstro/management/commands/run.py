# coding=utf-8

import argparse

import tornado.ioloop
import tornado.httpserver

from monstro.core.app import application
from monstro.conf import settings


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

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
