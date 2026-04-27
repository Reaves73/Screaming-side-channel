#include "stdint.h"
#include "dacadc.h"

#include "stm32f3_hal_lowlevel.h"
#include "stm32f3xx_hal_rcc.h"
#include "stm32f3xx_hal_gpio.h"
#include "stm32f3xx_hal_dma.h"
#include "stm32f3xx_hal_uart.h"
#include "stm32f3xx_hal_flash.h"

void dac_gpio_init(){
    GPIO_InitTypeDef gpio;
    gpio.Pin  = GPIO_PIN_4;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &gpio);
}

void dac_init()
{
    // 1) Enable GPIOA clock
    __HAL_RCC_GPIOA_CLK_ENABLE();
    // 2) PA4 analog mode
    dac_gpio_init();
    // 3) Enable DAC clock
    RCC->APB1ENR |= RCC_APB1ENR_DAC1EN;
	DAC->DHR12R1 = 0;
    // 4) Enable DAC channel 1
    DAC->CR |= DAC_CR_EN1;
    // 5) Set mid-scale output
}

void dac_set(uint16_t value){
	if (value > 956) // 0.7V safety
	      value = 956;
        DAC->DHR12R1 = (value & (1024-1)); // 0,75V safety
}

//#define operating_voltage (3300)
//#define operating_voltage (2960)
#define operating_voltage (3200)
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
    // measure ouput voltage with ADC2_IN1 (also on PA4)

    // Enable GPIOA clock
    __HAL_RCC_GPIOA_CLK_ENABLE();

    // PA4 analog mode
    GPIO_InitTypeDef gpio;
    gpio.Pin  = GPIO_PIN_4;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &gpio);

  RCC->CFGR2 |= (0b10000 << 4); // Prescaler
  //RCC->CFGR2 |= (0b10000 << 9); // Prescaler

    // Enable ADC clock
    __HAL_RCC_ADC12_CLK_ENABLE();
    //RCC->AHBENR |= RCC_AHBENR_ADC12EN;

ADC12_COMMON->CCR |= (0b01 << 16); // 0b01

    // Disable ADC if enabled
    if (ADC2->CR & ADC_CR_ADEN) // BIT0
    {
        //printf("ADC turning off %x\n", rd32(ADC_CR));
        ADC2->CR |= ADC_CR_ADDIS; // BIT1
        while (ADC2->CR & ADC_CR_ADDIS);
    }
    //printf("ADC turned off\n");

/*
    // ADC clock = ADCCLK
    ADC2->CFGR2 &= ~ADC_CFGR2_CKMODE; // (BIT31 | BIT30)

    // Select channel 4 (PA4)
    ADC2->CHSELR = ADC_CHSELR_CHSEL4; // BIT4

    // Long sampling time (239.5 cycles)
    ADC2->SMPR = (ADC_SMPR_SMP_0 | ADC_SMPR_SMP_1 | ADC_SMPR_SMP_2); // 0x7

    // Calibrate ADC (recommended)
    ADC2->CR |= ADC_CR_ADCAL; // BIT31
    
    while (ADC2->CR & ADC_CR_ADCAL); // BIT31
    //printf("ADC calibrated\n");

    // Enable ADC
    ADC2->CR |= ADC_CR_ADEN; // BIT0

    while (!(ADC2->ISR & ADC_ISR_ADRDY)); // BIT0
    //printf("ADC enabled\n");
*/
    // Enable ADC voltage regulator
    ADC2->CR &= ~ADC_CR_ADVREGEN;
    ADC2->CR |= ADC_CR_ADVREGEN_0;
    for (volatile int i = 0; i < 100000; i++); // small delay


    // Calibrate ADC
    ADC2->CR &= ~ADC_CR_ADCALDIF; // single-ended
    ADC2->CR |= ADC_CR_ADCAL;
    while (ADC2->CR & ADC_CR_ADCAL);

    // Configure ADC
    ADC2->CFGR = 0; // default settings

    // Sampling time (long)
    ADC2->SMPR1 |= ADC_SMPR1_SMP4; // max sample time

    // Regular sequence: channel 4
    ADC2->SQR1 = (1 << ADC_SQR1_SQ1_Pos);

    // Enable ADC
    ADC2->CR |= ADC_CR_ADEN;
    while (!(ADC2->ISR & ADC_ISR_ADRDY));
}

uint16_t adc_get()
{
    // Start conversion
    ADC2->CR |= ADC_CR_ADSTART; // BIT2

    // Wait for end of conversion
    while (!(ADC2->ISR & ADC_ISR_EOC)); // BIT2

    // Read result
    return (uint16_t)(ADC2->DR);
}

uint16_t adc_get_mv()
{
    uint16_t adc_val = adc_get();
    //printf("adc raw: %d\n", adc_val);
    return (uint16_t)(((uint32_t)adc_val) * operating_voltage / 4095);
}

void dacadc_init() {
    dac_init();
    adc_init();
}

