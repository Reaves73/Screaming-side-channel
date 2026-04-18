#ifndef HAL_EXTRA_H
#define HAL_EXTRA_H

#include "stdint.h"

void dac_init(void);
void dac_gpio_init_first(void);
void dac_gpio_init(void);
void switcher_init(void);
void switcher_set(int i);

void delay_cycles(volatile uint32_t count);
void set_dac(int value);

#endif // HAL_EXTRA_H

