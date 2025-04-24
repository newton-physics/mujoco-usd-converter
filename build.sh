#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BUILD_VENV=${SCRIPT_DIR}/.build_venv
RUNTIME_VENV=${SCRIPT_DIR}/.runtime_venv

if [ $# -gt 0 ] && [ "$1" = "-c" ] || [ "$1" = "--clean" ]; then
    echo "Cleaning up..."
    rm -rf ${BUILD_VENV}
    rm -rf ${RUNTIME_VENV}
    rm -rf dist
fi

# setup the build environment
if [ -d "${BUILD_VENV}" ]; then
    source ${BUILD_VENV}/bin/activate
else
    echo "Building: ${BUILD_VENV}"
    python -m venv ${BUILD_VENV}
    source ${BUILD_VENV}/bin/activate
    python -m pip install poetry
fi

# do the build
echo Using `poetry --version`
if [ -d ${SCRIPT_DIR}/dist ]; then
    rm -rf ${SCRIPT_DIR}/dist
fi
poetry build

# prepare the runtime environment
if [ -d "${RUNTIME_VENV}" ]; then
    source ${RUNTIME_VENV}/bin/activate
    # install the artifact to the runtime
    python -m pip install ${SCRIPT_DIR}/dist/mjc_usd_converter-*.whl --no-deps --force-reinstall
else
    echo "Building: ${RUNTIME_VENV}"
    python -m venv ${RUNTIME_VENV}
    source ${RUNTIME_VENV}/bin/activate
    python -m pip install ${SCRIPT_DIR}/dist/mjc_usd_converter-*.whl
fi
