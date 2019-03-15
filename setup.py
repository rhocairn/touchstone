#!/usr/bin/env python
import re
from glob import glob
from os import path

import os.path
from setuptools import (
    find_packages,
    setup,
)

ROOTDIR = os.path.abspath(os.path.dirname(__file__))


def find_version(*path: str) -> str:
    with open(os.path.join(ROOTDIR, *path), 'r') as fp:
        version_file = fp.read()

    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Read the README file
with open(path.join(ROOTDIR, 'README.md'), encoding='utf-8') as fp:
    long_description = fp.read()

install_requires = [
    'dataclasses',
]

tests_requires = [
    'pytest==4.*',
    'tox==3.*',
    'flake8==3.6.*',
    'flake8-tuple',
    'mypy',
    'docutils',
]

dist_requires = [
    'setuptools >= 38.6.0',
    'wheel >= 0.31.0',
    'twine >= 1.11.0',
]

django_requires = [
    'django == 2.*',
]

setup(
    name='touchstone',
    description="IoC framework driven by annotations and type hints",
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=find_version('src', 'touchstone', 'version.py'),
    url='https://github.com/gmaybrun/touchstone',
    maintainer='gmaybrun@gmail.com',
    maintainer_email='gmaybrun@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob('src/*.py')],
    zip_safe=True,
    install_requires=install_requires,
    tests_require=tests_requires,
    extras_require={
        'tests': tests_requires,
        'dist': dist_requires,
        'django': django_requires,
    },
    package_data={
        'touchstone': ['py.typed'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Object Brokering',
        'Topic :: Utilities',
        'Typing :: Typed',
    ],
)
