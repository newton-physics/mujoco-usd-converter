#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
RUNTIME_VENV=${SCRIPT_DIR}/.runtime_venv

if [ -d "${RUNTIME_VENV}" ]; then
    source ${RUNTIME_VENV}/bin/activate
else
    source ${SCRIPT_DIR}/build.sh
fi

mjc_usd_converter
