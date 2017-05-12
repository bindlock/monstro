import nose

import tornado.ioloop

from monstro.conf import settings
from monstro.management import Command
from monstro.db import databases


class Test(Command):

    def add_arguments(self, parser):
        parser.add_argument('modules', nargs='*')

    def execute(self, arguments):
        database = databases.get()
        test_database = database.client['test_{}'.format(database.name)]
        databases.set('default', test_database)

        argv = getattr(settings, 'nosetests_arguments', [])
        argv.extend(arguments.modules)

        nose.run(argv=argv)

        tornado.ioloop.IOLoop.current().run_sync(
            lambda: test_database.client.drop_database(test_database.name)
        )
