#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
VENV=${SCRIPT_DIR}/.venv

if [ $# -gt 0 ] && [ "$1" = "-c" ] || [ "$1" = "--clean" ]; then
    echo "Cleaning..."
    rm -rf ${VENV}
    rm -rf dist
fi

# Ensure uv is available (for local development)
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed. Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies and build
echo "Installing dependencies with uv..."
uv sync --group dev

echo "Using uv version: $(uv --version)"
if [ -d ${SCRIPT_DIR}/dist ]; then
    rm -rf ${SCRIPT_DIR}/dist
fi
echo "Building wheel..."
uv build --wheel
