#include "stdint.h"
#include "miscgpio.h"

#include "stm32f0_hal_lowlevel.h"
#include "stm32f0xx_hal_rcc.h"
#include "stm32f0xx_hal_gpio.h"
#include "stm32f0xx_hal_dma.h"
#include "stm32f0xx_hal_uart.h"
#include "stm32f0xx_hal_flash.h"

void miscgpio_init() {
	GPIO_InitTypeDef gpio;

	// TODO: LED pin (should be the same)
	/*
	__HAL_RCC_GPIOC_CLK_ENABLE();
	gpio.Pin  = GPIO_PIN_15;
 	gpio.Mode = GPIO_MODE_OUTPUT_PP;//GPIO_MODE_OUTPUT_PP, GPIO_MODE_OUTPUT_OD;
	gpio.Pull = GPIO_NOPULL; //GPIO_NOPULL, GPIO_PULLUP, GPIO_PULLDOWN
	HAL_GPIO_Init(GPIOC, &gpio);
	*/

	// previously used relay pin
	__HAL_RCC_GPIOB_CLK_ENABLE();
	gpio.Pin  = GPIO_PIN_9;
 	gpio.Mode = GPIO_MODE_OUTPUT_OD;
	gpio.Pull = GPIO_NOPULL;
	HAL_GPIO_Init(GPIOB, &gpio);
}

void miscgpio_led_set(uint8_t i) {
	// TODO: LED pin (should be the same)
	/*
	if (i) {
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_15, SET);
	} else {
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_15, RESET);
	}
	*/
}

/*
void miscgpio_relay_set(uint8_t i) {
	if (i) {
		HAL_GPIO_WritePin(GPIOB, GPIO_PIN_9, RESET);
	} else {
		HAL_GPIO_WritePin(GPIOB, GPIO_PIN_9, SET);
	}
}
*/

