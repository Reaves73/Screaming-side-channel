#!/usr/bin/env bash

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
REPO_DIR=$(readlink -f "${REPO_DIR}")

source ${REPO_DIR}/scripts/env.sh

cd ${REPO_DIR}/env/chipwhisperer
jupyter notebook
