#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
RUNTIME_VENV=${SCRIPT_DIR}/.runtime_venv
cd ${RUNTIME_VENV}
source bin/activate

# Run the tests
python -m unittest discover -v -s ${SCRIPT_DIR}/tests
