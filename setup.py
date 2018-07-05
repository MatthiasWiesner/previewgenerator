#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='preview_generator_service',
    version='0.1.0',
    description='This service generates preview images',
    author='matthias wiesner',
    packages=find_packages(exclude='tests'),
    install_requires=[
        'aio_pika',
        'pillow',
        'preview-generator',
        'untangle'
    ],
    entry_points={
        'console_scripts': [
            'previewgenerator=preview_generator_service.service:main'
        ]
    }
)
