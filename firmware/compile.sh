#!/usr/bin/env bash

# get firmware directory path
FIRMWARE_DIR=$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")
FIRMWARE_DIR=$(readlink -f "${FIRMWARE_DIR}")
cd ${FIRMWARE_DIR}

export MCUDIR=$(readlink -f "${FIRMWARE_DIR}/../env/chipwhisperer/firmware/mcu")
export DRIVERSDIR=$(readlink -f "${FIRMWARE_DIR}/drivers")

cd simpleserial-aes
make PLATFORM=CW308_STM32F0 CRYPTO_TARGET=TINYAES128C clean all

