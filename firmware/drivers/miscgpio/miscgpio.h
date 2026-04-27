#ifndef MISCGPIO_H
#define MISCGPIO_H

#include "stdint.h"

void delay_cycles(volatile uint32_t count);

void miscgpio_init();
void miscgpio_led_set(uint8_t i);

#endif // MISCGPIO_H

