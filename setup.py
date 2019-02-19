#!/usr/bin/env python3

from setuptools import setup
from dvbs2adduceremecum.forpip import git_describe


setup(
    name='dvbs2adduceremecum',
    version=git_describe(),
    description='DVB-S2 Adducere Mecum',
    long_description='',
    url='https://github.com/franalbani/dvbs2adduceremecum',
    author='Francisco Albani',
    license="?",
    author_email='',
    classifiers=[
        'Environment :: Console',
        'Operating System :: Linux',
        'Programming Language :: Python',
    ],
    # Beware of using find_packages.
    packages=[
        'dvbs2adduceremecum'
        ],
    install_requires=[
        'attrs',
        ],
    #   scripts=[
    #       ],
    #   data_files=[
    #       ('', glob('')),
    #       ],
)
