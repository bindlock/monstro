# coding=utf-8

import os
import argparse
import shutil

import monstro.management


def execute(args):
    templates = ('project', 'module')
    argparser = argparse.ArgumentParser(description='Create template')

    argparser.add_argument('template', choices=templates)
    argparser.add_argument('path')

    args = argparser.parse_args(args)

    template_path = os.path.join(
        os.path.abspath(os.path.dirname(monstro.management.__file__)),
        'templates/{}'.format(args.template)
    )
    destination_path = os.path.join(os.getcwd(), args.path)

    shutil.copytree(template_path, destination_path)
