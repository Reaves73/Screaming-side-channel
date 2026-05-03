#include "stdint.h"
#include "dacadc.h"

#include "stm32f3_hal_lowlevel.h"
#include "stm32f3xx_hal_rcc.h"
#include "stm32f3xx_hal_gpio.h"
#include "stm32f3xx_hal_dma.h"
#include "stm32f3xx_hal_uart.h"
#include "stm32f3xx_hal_flash.h"


void dac_set_gate(uint8_t on) {
    if (on) {
        DAC->CR |= DAC_CR_EN1;
    } else {
        DAC->CR &= ~DAC_CR_EN1;
    }
} 

void dac_init()
{
    // 3) Enable DAC clock
    RCC->APB1ENR |= RCC_APB1ENR_DAC1EN;
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

//#define operating_voltage (3300)
//#define operating_voltage (2960)
#define operating_voltage (3200)
#define operating_voltage_dac operating_voltage
//(operating_voltage-50)
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

    //RCC->CFGR2 |= (0b10000 << RCC_CFGR2_ADCPRE12_Pos); // Prescaler

    // Enable ADC clock
    __HAL_RCC_ADC12_CLK_ENABLE();

    ADC12_COMMON->CCR |= (0b01 << ADC12_CCR_CKMODE_Pos); // 0b01

    // Disable ADC if enabled
    if (ADC2->CR & ADC_CR_ADEN) // BIT0
    {
        //printf("ADC turning off %x\n", rd32(ADC_CR));
        ADC2->CR |= ADC_CR_ADDIS; // BIT1
        while (ADC2->CR & ADC_CR_ADDIS);
    }
    //printf("ADC turned off\n");

    // Enable ADC voltage regulator
    ADC2->CR &= ~ADC_CR_ADVREGEN;
    ADC2->CR |= ADC_CR_ADVREGEN_0;
    for (volatile int i = 0; i < 100000; i++); // small delay

    // Calibrate ADC
    ADC2->CR &= ~ADC_CR_ADCALDIF; // single-ended
    ADC2->CR |= ADC_CR_ADCAL;
    while (ADC2->CR & ADC_CR_ADCAL);
    //printf("ADC calibrated\n");

    // Configure ADC
    ADC2->CFGR = 0; // default settings

    // Sampling time (long - 601.5 clock cycles) at channel 1 (SMP1)
    ADC2->SMPR1 |= ADC_SMPR1_SMP1; // max sample time (0x7)

    // Regular sequence: channel 1
    ADC2->SQR1 = (1 << ADC_SQR1_SQ1_Pos);

    // Enable ADC
    ADC2->CR |= ADC_CR_ADEN;
    while (!(ADC2->ISR & ADC_ISR_ADRDY));
    //printf("ADC enabled\n");
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

