from tornado.util import import_object
import tornado.ioloop
import tornado.httpserver

from monstro.conf import settings
from monstro.core.app import application
from monstro.management import Command


class RunServer(Command):

    ioloop = tornado.ioloop.IOLoop.current()

    def add_arguments(self, parser):
        parser.add_argument('--host', default='127.0.0.1')
        parser.add_argument('--port', default=8000)

    def prepare_models(self):
        for path in getattr(settings, 'models', []):
            self.ioloop.spawn_callback(import_object(path).prepare)

    def execute(self, arguments):
        self.prepare_models()

        server = tornado.httpserver.HTTPServer(application)
        server.bind(address=arguments.host, port=arguments.port)
        server.start()

        print('Listen on http://{0.host}:{0.port}'.format(arguments))

        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            print('\n')
