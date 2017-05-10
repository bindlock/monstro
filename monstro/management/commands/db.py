import subprocess

from monstro.db import db


def execute(*args):
    subprocess.check_call(['mongo', db.database.name])
