#!/usr/bin/env python

import os

from setuptools import setup, find_packages

VERSION = '4.0.6'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASE_DIR, 'README.rst')) as f:
    LONG_DESCRIPTION = f.read()

REQUIRES = [
    'motor',
    'tornado',
]

if __name__ == '__main__':
    setup(
        name='monstro',
        version=VERSION,
        packages=find_packages(exclude=['tests*']),
        install_requires=REQUIRES,
        include_package_data=True,
        entry_points={
            'console_scripts': ['monstro = monstro.management:manage']
        },
        description='Web framework based on Tornado and MongoDB',
        long_description=LONG_DESCRIPTION,
        author='Vitalii Maslov',
        author_email='me@pyvim.com',
        url='https://github.com/pyvim/monstro',
        download_url='https://github.com/pyvim/monstro/tarball/master',
        license='MIT',
        keywords='framework, web, tornado, mongodb, motor, asynchronous',
        classifiers=[
            'Intended Audience :: Developers',
            'Programming Language :: Python :: 3',
        ],
    )
