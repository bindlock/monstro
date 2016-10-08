# coding=utf-8

import os
import sys
import argparse
import importlib

from tornado.util import import_object

from monstro.core.constants import (
    SETTINGS_ENVIRONMENT_VARIABLE,
    MONGODB_URI_ENVIRONMENT_VARIABLE
)


def manage():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('command')
    argparser.add_argument('-s', '--settings')
    argparser.add_argument('-p', '--python-path')
    argparser.add_argument('-m', '--mongodb-uri')

    args, unknown = argparser.parse_known_args()

    if args.settings:
        os.environ[SETTINGS_ENVIRONMENT_VARIABLE] = args.settings

    if args.mongodb_uri:
        os.environ[MONGODB_URI_ENVIRONMENT_VARIABLE] = args.mongodb_uri

    if args.python_path:
        sys.path.insert(0, args.python_path)

    module_path = 'monstro.management.commands.{}.execute'.format(args.command)

    import_object(module_path)(unknown)
