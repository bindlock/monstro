# coding=utf-8

import subprocess

from monstro.conf import settings


def execute(args):
    subprocess.check_call(['mongo', settings.mongodb_database])
