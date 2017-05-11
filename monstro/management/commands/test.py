import nose

import tornado.ioloop

from monstro.conf import settings
from monstro.management import Command
import monstro.db.db


class Test(Command):

    def add_arguments(self, parser):
        parser.add_argument('modules', nargs='*')

    def execute(self, arguments):
        database_name = 'test_{}'.format(monstro.db.db.database.name)
        monstro.db.db.database = monstro.db.db.client[database_name]

        argv = getattr(settings, 'nosetests_arguments', [])
        argv.extend(arguments.modules)

        nose.run(argv=argv)

        tornado.ioloop.IOLoop.current().run_sync(
            lambda: monstro.db.db.client.drop_database(database_name)
        )
