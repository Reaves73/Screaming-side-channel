#ifndef DACADC_H
#define DACADC_H

#include "stdint.h"

void dac_soldertest(void (*_delay_cycles)(volatile uint32_t), void (*_miscgpio_led_set)(uint8_t,uint8_t));

void dacadc_init();
void dac_set_gate(uint8_t on);
void dac_set_mv(uint16_t value);
void dac_trigger();
uint16_t adc_get_mv();

#endif // DACADC_H

