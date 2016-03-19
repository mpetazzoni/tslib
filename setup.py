#!/usr/bin/env python

# Copyright (C) 2016 SignalFx, Inc. All rights reserved.

from setuptools import setup, find_packages

import tslib

with open('README.rst') as readme:
    long_description = readme.read()

setup(
    name='tslib',
    version=tslib.__version__,
    author='Maxime Petazzoni',
    author_email='maxime.petazzoni@bulix.org',
    description=('A library for dealing with human-readable '
                 'time offsets and timestamps'),
    license='Apache Software License v2',
    long_description=long_description,
    zip_safe=True,
    packages=find_packages(),
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': ['ts=tslib:main'],
    },
    url='https://github.com/mpetazzoni/tslib',
)
