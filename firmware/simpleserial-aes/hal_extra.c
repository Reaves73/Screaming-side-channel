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

void set_dac(int value){
	if(value>2048){
	DAC->DHR12R1 = 2048;
	}
	else{
	DAC->DHR12R1 = value;
	}
}

