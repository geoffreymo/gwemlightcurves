#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Michael Coughlin (2021)
#
# This file is part of gwemlightcurves.
#
# gwemopt is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwemopt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwemopt.  If not, see <http://www.gnu.org/licenses/>.

"""Setup the gwemlightcurves package
"""

# ignore all invalid names (pylint isn't good at looking at executables)
# pylint: disable=invalid-name

from __future__ import print_function

import os, sys
from distutils.version import LooseVersion

from setuptools import (setup, find_packages,
                        __version__ as setuptools_version)

def get_scripts(scripts_dir='bin'):
    """Get relative file paths for all files under the ``scripts_dir``
    """ 
    scripts = []
    for (dirname, _, filenames) in os.walk(scripts_dir):
        scripts.extend([os.path.join(dirname, fn) for fn in filenames])
    return scripts

import versioneer
#from setup_utils import (CMDCLASS, get_setup_requires, get_scripts)
__version__ = versioneer.get_version()
CMDCLASS=versioneer.get_cmdclass()

# -- dependencies -------------------------------------------------------------

# build dependencies
#setup_requires = get_setup_requires()

# package dependencies
install_requires = [
    'numpy',
    'scipy',
    'astropy',
    'h5py',
    'pandas',
    'george',
    'h5py',
    'scikit-learn>=0.18',
    'matplotlib',
    'sncosmo',
    'pymultinest',
    'requests',
    'penquins',
    'afterglowpy',
    'Cython',
    'extinction',
]

# test dependencies
tests_require = [
    'pytest>=3.1',
    'pytest-runner',
    'freezegun',
    'sqlparse',
    'bs4',
]
if sys.version < '3':
    tests_require.append('mock')

# -- run setup ----------------------------------------------------------------

setup(
    # metadata
    name='gwemlightcurves',
    provides=['gwemlightcurves'],
    version=__version__,
    description="A python package for kilonova lightcurves",
    long_description=("gwemopt is a python package for kilonova lightcurves"),
    author='Michael Coughlin',
    author_email='michael.coughlin@ligo.org',
    license='GPLv3',
    url='https://github.com/mcoughlin/gwemlightcurves/',

    # package content
    packages=find_packages(),
    scripts=get_scripts(),
    include_package_data=True,

    # dependencies
    cmdclass=CMDCLASS,
    install_requires=install_requires,
    tests_require=tests_require,

    # classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Science/Research',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
)
