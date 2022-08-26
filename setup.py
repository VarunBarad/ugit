#!/usr/bin/env python3

from setuptools import setup

setup(
    name='ugit',
    version='1.0',
    packages=['ugit'],
    entry_ppoints={
        'console_scripts': [
            'ugit = ugit.cli:main',
        ],
    },
)
