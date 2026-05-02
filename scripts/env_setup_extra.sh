#!/usr/bin/env bash

# exit immediately if an error happens
set -e

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
ENV_DIR=$(readlink -f "${REPO_DIR}/env")

source ${ENV_DIR}/.cwvenv/bin/activate

python -m pip install nanpy

#python -m pip install gnuradio
#python -m pip install PyQt5

echo ""
echo "env_setup_extra.sh completed!"
