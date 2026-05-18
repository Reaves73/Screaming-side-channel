#include "stdint.h"
#include "dacadc.h"

#include "stm32l4xx_hal_rcc.h"
#include "stm32l4xx_hal_gpio.h"

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
    return 0;
}

uint16_t adc_get_mv()
{
    return 0;
}

void dacadc_init() {
}

// -----------------------------------

void soldering_pintest_init() {
	GPIO_InitTypeDef gpio;

	// DAC
	__HAL_RCC_GPIOA_CLK_ENABLE();
	// DAC channel 1
	gpio.Pin  = GPIO_PIN_4;
 	gpio.Mode = GPIO_MODE_INPUT;
	gpio.Pull = GPIO_PULLDOWN; //GPIO_NOPULL, GPIO_PULLUP, GPIO_PULLDOWN
	HAL_GPIO_Init(GPIOA, &gpio);

	// DAC channel 2
	gpio.Pin  = GPIO_PIN_5;
 	gpio.Mode = GPIO_MODE_INPUT;
	gpio.Pull = GPIO_PULLDOWN; //GPIO_NOPULL, GPIO_PULLUP, GPIO_PULLDOWN
	HAL_GPIO_Init(GPIOA, &gpio);
}

uint8_t soldering_pintest_read() {
    uint8_t v = 0;
    v |= ((HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_4) == GPIO_PIN_SET) & 0x1) << 0;
    v |= ((HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_5) == GPIO_PIN_SET) & 0x1) << 1;
    return v;
}

void soldering_pintest_led_set(void (*_miscgpio_led_set)(uint8_t,uint8_t), uint8_t v) {
    miscgpio_led_set(1, v & 0x1);
    miscgpio_led_set(2, v & 0x2);
}


void soldering_pintest_trial(uint8_t v) {
	GPIO_InitTypeDef gpio;
	
	// DAC channel 1
	gpio.Pin  = GPIO_PIN_4;
 	gpio.Mode = GPIO_MODE_INPUT;
	if (v) {
		gpio.Pull = GPIO_PULLUP;
	} else {
		gpio.Pull = GPIO_PULLDOWN;
	}
	HAL_GPIO_Init(GPIOA, &gpio);
	
	// DAC channel 2
	gpio.Pin  = GPIO_PIN_5;
 	gpio.Mode = GPIO_MODE_INPUT;
	if (v) {
		gpio.Pull = GPIO_PULLDOWN;
	} else {
		gpio.Pull = GPIO_PULLUP;
	}
	HAL_GPIO_Init(GPIOA, &gpio);
}

void dac_soldertest(void (*_delay_cycles)(volatile uint32_t), void (*_miscgpio_led_set)(uint8_t,uint8_t)) {
    soldering_pintest_init();
	while(1) {
		_miscgpio_led_set(0, 0);
		soldering_pintest_trial(0);
		_delay_cycles(1000000/2);
        soldering_pintest_led_set(_miscgpio_led_set, soldering_pintest_read());
		_delay_cycles(1000000/2);

		_miscgpio_led_set(0, 1);
		soldering_pintest_trial(1);
		_delay_cycles(1000000/2);
        soldering_pintest_led_set(_miscgpio_led_set, soldering_pintest_read());
		_delay_cycles(1000000/2);
	}
}
