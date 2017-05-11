import subprocess

from monstro.db import db
from monstro.management import Command


class DatabaseShell(Command):

    def execute(self, arguments):
        subprocess.check_call(['mongo', db.database.name])
