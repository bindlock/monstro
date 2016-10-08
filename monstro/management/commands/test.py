# coding=utf-8

import os

import nose

from monstro.conf import settings
from monstro.core.constants import (
    TEST_MONGODB_URI, MONGODB_URI_ENVIRONMENT_VARIABLE
)


def execute(args):
    os.environ.setdefault(MONGODB_URI_ENVIRONMENT_VARIABLE, TEST_MONGODB_URI)
    nose.run(argv=getattr(settings, 'nosetests_arguments', []))
