import tornado.ioloop
import tornado.httpserver

from monstro.core.app import application
from monstro.management import Command


class RunServer(Command):

    def add_arguments(self, parser):
        parser.add_argument('--host', default='127.0.0.1')
        parser.add_argument('--port', default=8000)

    def execute(self, arguments):
        server = tornado.httpserver.HTTPServer(application)
        server.bind(address=arguments.host, port=arguments.port)
        server.start()

        print('Listen on http://{0.host}:{0.port}'.format(arguments))

        try:
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            print('\n')
