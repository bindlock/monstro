# coding=utf-8

import os

from setuptools import setup, find_packages

VERSION = '1.0.5'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASE_DIR, 'README.rst')) as f:
    LONG_DESCRIPTION = f.read()

REQUIRES = [
    'motor',
    'tornado',
]

setup(
    name='monstro',
    version=VERSION,
    packages=find_packages(),
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
    keywords='framework, web, tornado, mongodb, motor, server, asynchronous',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
)
