#!/usr/bin/env bash

# exit immediately if an error happens
set -e

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
ENV_DIR=$(readlink -f "${REPO_DIR}/env")

mkdir -p ${ENV_DIR}

#rm -rf ${ENV_DIR}/chipwhisperer
git clone https://github.com/newaetech/chipwhisperer ${ENV_DIR}/chipwhisperer
cd ${ENV_DIR}/chipwhisperer
git checkout v6.0.0b
git submodule update --init --recursive

python3 -m venv ${ENV_DIR}/.cwvenv
source ${ENV_DIR}/.cwvenv/bin/activate

git submodule update --init jupyter

python -m pip install -e .
python -m pip install -r jupyter/requirements.txt

echo ""
echo "env_setup.sh completed!"
