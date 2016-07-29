#!/usr/bin/env python
# coding=utf-8

import nose

from monstro.conf import settings


def execute(args):
    nose.run(argv=getattr(settings, 'test_settings', []))
