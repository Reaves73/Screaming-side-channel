#include "stdint.h"
#include "dacadc.h"

void dac_set_gate(uint8_t on) {
}

void dac_init()
{
}

void dac_set(uint16_t value){
}

#define DAC_TRIGGER_OFFSET 40
#define DAC_TRIGGER_DELAYCOUNT 5000
void dac_trigger() {
}

//#define operating_voltage (3300)
#define operating_voltage (2960)
#define operating_voltage_dac (operating_voltage-50)
void dac_set_mv(uint16_t value)
{
}

// -------------------------------

void adc_init()
{
}

uint16_t adc_get()
{
}

uint16_t adc_get_mv()
{
}

void dacadc_init() {
}

