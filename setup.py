#!/usr/bin/env python

from setuptools import setup

VERSION = "0.1.0"


with open('README.rst') as f:
    LONG_DESCR = f.read()

data_files = []

setup(
    name='mcpgui',
    version=VERSION,
    description='Fuzzball GUI package for the Mud Client Protocol.',
    long_description=LONG_DESCR,
    author='Revar Desmera',
    author_email='revarbat@gmail.com',
    url='https://github.com/revarbat/mcpgui',
    download_url='https://github.com/revarbat/mcpgui/archive/master.zip',
    packages=['mcpgui'],
    license='BSD 2-clause',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
    ],
    keywords='mcp mud client gui',
    install_requires=['setuptools'],
    data_files=data_files,
)
