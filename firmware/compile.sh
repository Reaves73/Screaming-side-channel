%%bash
#cd ../../firmware/mcu/simpleserial-base/
cd ../../firmware/mcu/simpleserial-aes/
make PLATFORM=CW308_STM32F0 CRYPTO_TARGET=TINYAES128C
