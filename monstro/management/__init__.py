# coding=utf-8

import os
import sys
import argparse
import importlib

from tornado.util import import_object
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE


def manage():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('command')
    argparser.add_argument('-s', '--settings')
    argparser.add_argument('-p', '--python-path')

    args, unknown = argparser.parse_known_args()

    if args.settings:
        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = args.settings

    if args.python_path:
        sys.path.insert(0, args.python_path)

    module_path = 'monstro.management.commands.{}.execute'.format(args.command)

    import_object(module_path)(unknown)
