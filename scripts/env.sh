#!/usr/bin/env bash

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
ENV_DIR=$(readlink -f "${REPO_DIR}/env")

# script needs to run sourced
if [[ "$0" == "$BASH_SOURCE" ]]; then
  echo "ERROR: script is not sourced"
  exit 1
fi

source ${ENV_DIR}/.cwvenv/bin/activate
