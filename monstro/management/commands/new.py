import os
import shutil

import monstro.management


class NewTemplate(monstro.management.Command):

    templates = ('project', 'module')

    def add_arguments(self, parser):
        parser.add_argument('template', choices=self.templates)
        parser.add_argument('path')

    def execute(self, arguments):
        source = os.path.join(
            os.path.abspath(os.path.dirname(monstro.management.__file__)),
            'templates/{}'.format(arguments.template)
        )
        destination = os.path.join(os.getcwd(), arguments.path)

        shutil.copytree(source, destination)
