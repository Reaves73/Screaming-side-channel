#include "stdint.h"
#include "miscgpio.h"

/*#include "stm32f3_hal_lowlevel.h"*/
#include "stm32f3xx_hal_rcc.h"
#include "stm32f3xx_hal_gpio.h"
/*#include "stm32f3xx_hal_dma.h"
#include "stm32f3xx_hal_uart.h"
#include "stm32f3xx_hal_flash.h"*/

void miscgpio_init() {
	GPIO_InitTypeDef gpio;

	// LED pins
	__HAL_RCC_GPIOC_CLK_ENABLE();
	gpio.Pin  = GPIO_PIN_15;
 	gpio.Mode = GPIO_MODE_OUTPUT_PP;//GPIO_MODE_OUTPUT_PP, GPIO_MODE_OUTPUT_OD;
	gpio.Pull = GPIO_NOPULL; //GPIO_NOPULL, GPIO_PULLUP, GPIO_PULLDOWN
	HAL_GPIO_Init(GPIOC, &gpio);
	gpio.Pin  = GPIO_PIN_14;
	HAL_GPIO_Init(GPIOC, &gpio);
	gpio.Pin  = GPIO_PIN_13;
	HAL_GPIO_Init(GPIOC, &gpio);

	miscgpio_led_set(0, 0);
	miscgpio_led_set(1, 0);
	miscgpio_led_set(2, 0);
}

void miscgpio_led_set(uint8_t id, uint8_t on) {
	GPIO_PinState ps;
	if (on) {
		ps = SET;
	} else {
		ps = RESET;
	}
	switch (id) {
		case 0:
			HAL_GPIO_WritePin(GPIOC, GPIO_PIN_15, ps);
		    break;
		case 1:
			HAL_GPIO_WritePin(GPIOC, GPIO_PIN_14, ps);
		    break;
		case 2:
			HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, ps);
		    break;
		default:
		    while (1); // wrong id
	}
}

