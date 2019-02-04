#!/usr/bin/env python
import os.path
import re
from glob import glob

from setuptools import (
    find_packages,
    setup,
)


def find_version(*path) -> str:
    rootdir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(rootdir, *path), 'r') as fp:
        version_file = fp.read()

    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


install_requires = []  # type: ignore

tests_requires = [
    'pytest==4.*',
    'tox==3.*',
    'flake8==3.6.*',
    'flake8-tuple',
    'mypy',
    'docutils',
]

setup(
    name='py-ioc',
    version=find_version('src', 'py_ioc', 'version.py'),
    url='https://github.com/gmaybrun/?',
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
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
