#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
VENV=${SCRIPT_DIR}/.venv

if [ $# -gt 0 ] && [ "$1" = "-c" ] || [ "$1" = "--clean" ]; then
    echo "Cleaning..."
    rm -rf ${VENV}
    rm -rf dist
fi

# setup the build environment
if [ -d "${VENV}" ]; then
    source ${VENV}/bin/activate
else
    echo "Building: ${VENV}"
    python -m venv ${VENV}
    source ${VENV}/bin/activate
    python -m pip install poetry
fi

# do the build
echo Using `poetry --version`
if [ -d ${SCRIPT_DIR}/dist ]; then
    rm -rf ${SCRIPT_DIR}/dist
fi
poetry build --format=wheel
poetry lock
poetry install
