#!/usr/bin/env bash

set -euxo pipefail

VERSION="$(python setup.py --version)"
TAG="v${VERSION}"

rm -rf dist/
python setup.py sdist bdist_wheel
twine check dist/*
python -m twine upload dist/*

git tag -a "${TAG}" -m "Release v${VERSION}"
git push origin "${TAG}"
