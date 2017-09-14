import os

import nose

from monstro.conf import settings
from monstro.core.constants import TEST_ENVIRONMENT_VARIABLE
from monstro.management import Command


class Test(Command):

    def add_arguments(self, parser):
        parser.add_argument('modules', nargs='*')

    def execute(self, arguments):
        os.environ[TEST_ENVIRONMENT_VARIABLE] = 'True'
        argv = getattr(settings, 'nosetests_arguments', [])
        argv.extend(arguments.modules)

        nose.run(argv=argv)
