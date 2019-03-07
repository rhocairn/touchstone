#!/usr/bin/env bash

set -euxo pipefail

rm -rf dist/
python setup.py sdist bdist_wheel
twine check dist/*
python -m twine upload dist/*
