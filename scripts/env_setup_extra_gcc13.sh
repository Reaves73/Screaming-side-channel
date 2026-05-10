#!/usr/bin/env bash

# exit immediately if an error happens
set -e

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
ENV_DIR=$(readlink -f "${REPO_DIR}/env")

cd ${ENV_DIR}
mkdir gcc13
cd gcc13
wget "https://developer.arm.com/-/media/Files/downloads/gnu/13.3.rel1/binrel/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi.tar.xz"
tar xf arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi.tar.xz


echo ""
echo "env_setup_extra.sh completed!"
