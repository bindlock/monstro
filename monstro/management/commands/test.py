import nose

from monstro.conf import settings
from monstro.management import Command


class Test(Command):

    def add_arguments(self, parser):
        parser.add_argument('modules', nargs='*')

    def execute(self, arguments):
        argv = getattr(settings, 'nosetests_arguments', [])
        argv.extend(arguments.modules)

        nose.run(argv=argv)
