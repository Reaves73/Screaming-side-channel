#include "stdint.h"
#include "dacadc.h"

#include "stm32l4xx_hal_rcc.h"
#include "stm32l4xx_hal_gpio.h"

void dac_set_gate(uint8_t on) {
    if (on) {
        DAC->CR |= DAC_CR_EN1;
    } else {
        DAC->CR &= ~DAC_CR_EN1;
    }
}

void dac_init()
{
    // DAC1_OUT1 on PA4

    // 3) Enable DAC clock
    __HAL_RCC_DAC1_CLK_ENABLE();
	DAC->DHR12R1 = 0;
    // 4) Enable DAC channel 1
    dac_set_gate(0);
    // 5) Set mid-scale output
}

void dac_set(uint16_t value){
	if (value > 956) // 0.7V safety
	      value = 956;
        DAC->DHR12R1 = (value & (1024-1)); // 0,75V safety
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
    //dac_set(1383); // 1.0V (@VDD 2.96V)
    //dac_set(692);  // 0.5V (@VDD 2.96V)
    uint16_t dac_value;
    if (value > operating_voltage_dac) {
        dac_value = 4095;
    } else {
        dac_value = (((uint32_t)value) * (4095*1000/operating_voltage_dac)) / (1000);
    }
    if (value > 700) {
        dac_set(0);
        //printf("\n!!!overshooting!!! %d\n", dac_value);
        while (1);
    }
    //printf("dac_value: %d\n", dac_value);
    dac_set(dac_value);
}

// -------------------------------

void adc_init()
{
    // measure ouput voltage with ADC1_IN9 (also on PA4)

    //RCC->CFGR2 |= (0b10000 << RCC_CFGR2_ADCPRE12_Pos); // Prescaler

    // Enable ADC clock
    __HAL_RCC_ADC_CLK_ENABLE();
    //RCC->CCIPR |= RCC_CCIPR_ADCSEL;

    ADC1_COMMON->CCR |= (0b01 << ADC_CCR_CKMODE_Pos); // 0b01
    //ADC1_COMMON->CCR |= ADC_CCR_TSEN; // enable temperature sensor

    // Disable ADC if enabled
    if (ADC1->CR & ADC_CR_ADEN) // BIT0
    {
        //printf("ADC turning off %x\n", rd32(ADC_CR));
        ADC1->CR |= ADC_CR_ADDIS; // BIT1
        while (ADC1->CR & ADC_CR_ADDIS);
    }
    //printf("ADC turned off\n");

    // disable deep power down mode
    ADC1->CR &= ~ADC_CR_DEEPPWD;

    // Enable ADC voltage regulator
    ADC1->CR &= ~ADC_CR_ADVREGEN;
    ADC1->CR |= ADC_CR_ADVREGEN;
    for (volatile int i = 0; i < 100000; i++); // small delay

    // Calibrate ADC
    ADC1->CR &= ~ADC_CR_ADCALDIF; // single-ended
    ADC1->CR |= ADC_CR_ADCAL;
    while (ADC1->CR & ADC_CR_ADCAL);
    //printf("ADC calibrated\n");

    // Configure ADC
    ADC1->CFGR = 0; // default settings

    // Sampling time (long - 601.5 clock cycles) at channel 1 (SMP1)
    ADC1->SMPR1 |= (0b111 << ADC_SMPR1_SMP9_Pos); // max sample time (0x7)

    // Regular sequence: channel 9
    ADC1->SQR1 =
    (9 << ADC_SQR1_SQ1_Pos) |   // channel 9
    //(17 << ADC_SQR1_SQ1_Pos) |   // channel 17
    (0 << ADC_SQR1_L_Pos);      // 1 conversion
    // channel 17 is either temperature sensor if enabled, or otherwise it is dac_out1

    // Enable ADC
    ADC1->CR |= ADC_CR_ADEN;
    while (!(ADC1->ISR & ADC_ISR_ADRDY));
    //printf("ADC enabled\n");
}

uint16_t adc_get()
{
    // Start conversion
    ADC1->CR |= ADC_CR_ADSTART; // BIT2

    // Wait for end of conversion
    while (!(ADC1->ISR & ADC_ISR_EOC)); // BIT2

    // Read result
    return (uint16_t)(ADC1->DR);
}

uint16_t adc_get_mv()
{
    uint16_t adc_val = adc_get();
    //printf("adc raw: %d\n", adc_val);
    return (uint16_t)(((uint32_t)adc_val) * operating_voltage / 4095);
}

void dacadc_init() {
    // Enable GPIOA clock
    __HAL_RCC_GPIOA_CLK_ENABLE();

    // PA4 analog mode
    GPIO_InitTypeDef gpio;
    gpio.Pin  = GPIO_PIN_4;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &gpio);

    dac_init();
    adc_init();
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
