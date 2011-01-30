import os
from setuptools import setup, find_packages

version = '0.1.0'

description = "A command-line program for managing dotfiles."

setup(
    name = "dotfiler",
    version = version,
    url = '',
    license = '',
    description = description,
    long_description = description,
    author = 'Carl Baatz',
    author_email = 'carl.baatz@gmail.com',
    packages = find_packages('src'),
    package_dir = {'': 'dist'},
    install_requires = ['setuptools'],
    entry_points="""
    [console_scripts]
    dotfiler = dotfiler:main
    """,
    classifiers=[
    ],
    test_suite = 'nose.collector',
)

