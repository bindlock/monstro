# coding=utf-8

import subprocess

from monstro.orm import db


def execute(args):
    subprocess.check_call(['mongo', db.database.name])
