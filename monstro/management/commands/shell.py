import code

from monstro.management import Command


class Shell(Command):

    def execute(self, arguments):
        code.interact()
