#!/usr/bin/env python

import os
import sys
sys.path.insert(0, 'modules')

import monstro.management
from monstro.core.constants import SETTINGS_ENVIRONMENT_VARIABLE


if __name__ == '__main__':
    os.environ.setdefault(
        SETTINGS_ENVIRONMENT_VARIABLE, 'settings.development.Settings'
    )

    monstro.management.manage()
