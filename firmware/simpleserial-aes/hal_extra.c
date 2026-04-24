#include "stdint.h"
#include "hal_extra.h"

#include "stm32f0_hal_lowlevel.h"
#include "stm32f0xx_hal_rcc.h"
#include "stm32f0xx_hal_gpio.h"
#include "stm32f0xx_hal_dma.h"
#include "stm32f0xx_hal_uart.h"
#include "stm32f0xx_hal_flash.h"

void delay_cycles(volatile uint32_t count)
{
    while(count--) {
        __asm__("nop");
    }
}

void switcher_init(void) {
	__HAL_RCC_GPIOB_CLK_ENABLE();
	GPIO_InitTypeDef gpio;
	gpio.Pin  = GPIO_PIN_9;
 	gpio.Mode = GPIO_MODE_OUTPUT_OD;
    gpio.Pull = GPIO_NOPULL;
	HAL_GPIO_Init(GPIOB, &gpio);
}

void switcher_set(int i) {
	if(i==1){
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_9, RESET);
	}
	else if(i==0){
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_9, SET);
	}
}

void dac_gpio_init_first(void){
	GPIO_InitTypeDef gpio;
    gpio.Pin  = GPIO_PIN_4;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &gpio);
}

void dac_gpio_init(void){
	GPIO_InitTypeDef gpio;
    gpio.Pin  = GPIO_PIN_4;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &gpio);
}

void dac_init(void)
{
    // 1) Enable GPIOA clock
    __HAL_RCC_GPIOA_CLK_ENABLE();
    // 2) PA4 analog mode
	//dac_gpio_init();
    // 3) Enable DAC clock
    RCC->APB1ENR |= RCC_APB1ENR_DACEN;
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
        printf("\n!!!overshooting!!!\n", dac_value);
        while (1);
    }
    //printf("dac_value: %d\n", dac_value);
    dac_set(dac_value);
}

