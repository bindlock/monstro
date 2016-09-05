#!/usr/bin/env python
# coding=utf-8

import os

import nose

from monstro.conf import settings


def execute(args):
    os.environ['DB'] = '__monstro__'
    nose.run(argv=getattr(settings, 'test_settings', []))
