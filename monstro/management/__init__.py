import argparse
import functools
import importlib
import os
import sys


from tornado.util import import_object

from monstro.conf import settings
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE


class Command(object):

    def get_argument_parser(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('command')
        parser.add_argument('-s', '--settings')
        parser.add_argument('-p', '--python-path')

        self.add_arguments(parser)

        return parser

    def add_arguments(self, parser):
        pass

    def execute(self, arguments):
        raise NotImplementedError()


def manage():
    commands = {
        'db': 'monstro.management.commands.db.DatabaseShell',
        'migrate': 'monstro.management.commands.migrate.ApplyMigrations',
        'new': 'monstro.management.commands.new.NewTemplate',
        'run': 'monstro.management.commands.run.RunServer',
        'shell': 'monstro.management.commands.shell.Shell',
        'test': 'monstro.management.commands.test.Test',
    }

    commands.update(getattr(settings, 'commands', {}))

    arguments, __ = Command().get_argument_parser().parse_known_args()

    try:
        command = import_object(commands[arguments.command])
    except KeyError:
        print('Unknown command: {}'.format(arguments.command))

    if arguments.settings:
        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = arguments.settings

    if arguments.python_path:
        sys.path.insert(0, arguments.python_path)

    command().execute(command().get_argument_parser().parse_args())
