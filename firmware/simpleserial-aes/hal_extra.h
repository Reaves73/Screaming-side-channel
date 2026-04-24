#ifndef HAL_EXTRA_H
#define HAL_EXTRA_H

#include "stdint.h"

void dac_init(void);
void dac_set(uint16_t value);
void dac_set_mv(uint16_t value);

void adc_init();
uint16_t adc_get();
uint16_t adc_get_mv();

void delay_cycles(volatile uint32_t count);

void relay_init(void);
void relay_set(int i);

#endif // HAL_EXTRA_H

