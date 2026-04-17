#!/usr/bin/env bash

# exit immediately if an error happens
set -e

# get env directory path
REPO_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/..
ENV_DIR=$(readlink -f "${REPO_DIR}/env")

cd ${ENV_DIR}/chipwhisperer
cp 50-newae.rules /etc/udev/rules.d/50-newae.rules
udevadm control --reload-rules
groupadd -fr chipwhisperer # new systemd versions require system accounts for udev

# for each user:
#usermod -aG chipwhisperer $USER
#usermod -aG plugdev $USER
