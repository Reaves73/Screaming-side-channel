/*
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

void soldering_pintest() {
	while(1) {
		miscgpio_led_set(0);
		soldering_pintest_trial(0);
		delay_cycles(1000000);
		miscgpio_led_set(1);
		soldering_pintest_trial(1);
		delay_cycles(1000000);
	}
}
*/
