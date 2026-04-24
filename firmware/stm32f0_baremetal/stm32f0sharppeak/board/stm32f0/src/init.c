/*
 * Author: Aurelio Colosimo, 2016
 * Originally modified from kim-os project:
 * https://github.com/colosimo/kim-os
 */

#include <gpio.h>
#include <stm32f411x.h>
#include "lib/printf.h"

#define attr_sect(x) __attribute__((section(x))) \
    __attribute__((aligned(4))) \
    __attribute__((used))

#define STACK_TOP ((void*)(0x20002000))

/* NOTE: The following values are hard-coded defines according to isr_reset
 * code. I'm lazy, so isr_reset is not actually using the defines, but the
 * values below are the result of isr_reset clock settings commands */
#define HSE_FREQ   8000000 /* 8MHz external crystal */
#define PLLMUL           6
#define CPU_FREQ   (HSE_FREQ * PLLMUL)
#define AHB_PRESCALER 1
#define APB_PRESCALER 1
#define HCLCK (CPU_FREQ / AHB_PRESCALER)
#define PCLK (HCLK / APB_PRESCALER)
#define SYSTICKS_FREQ      1000

#define NO_FLASH_LATENCY 1

static uint32_t ticks = 0;

extern unsigned char _sdata_flash;
extern unsigned char _sdata;
extern unsigned char _edata;
extern unsigned char _sbss;
extern unsigned char _ebss;

extern int main();

void uart_init() {
	#ifdef NO_FLASH_LATENCY
		const int no_flash_latency = 1;
	#else
		const int no_flash_latency = 0;
	#endif

	/* Init USART1 on PA9/PA10 */
	gpio_func(IO(PORTA, 9), 1);
	gpio_func(IO(PORTA, 10), 1);
	gpio_mode(IO(PORTA, 9), PULL_NO);
	gpio_mode(IO(PORTA, 10), PULL_NO);

	/*  fPCLK=48MHz, br=115.2KBps, BRR=0x1A1, see table 104 pag. 704 */
	wr32(R_USART1_BRR, 0x1a1 / (no_flash_latency ? 6 : 1));
	or32(R_USART1_CR1, BIT3 | BIT2 | BIT0);

	// avoid receiving some wrong byte first, there must be a better way to fix this though
	for (int i = 0; i < 100; i++) {
		rd32(R_USART1_ISR);
		rd32(R_USART1_RDR);
	}
}

int uart_write(char c)
{
	/* Wait for data sent (TDR becomes empty */
	if (!(rd32(R_USART1_ISR) & BIT7))
		return -1;

	/* Write byte to tx register (TDR) */
	wr32(R_USART1_TDR, c);
	return 0;
}

int uart_read()
{
	/* wait for data to arrive */
	if (!(rd32(R_USART1_ISR) & BIT5))
		return -1;

	/* read byte from rx register (RDR) */
	return rd32(R_USART1_RDR)&0xFF;
}

void uart_putchar(char c) {
	while (uart_write(c));
}

char uart_getchar() {
	int c;
	while ((c = uart_read()) < 0);

	return (char)c;
}

#define DAC 0x40007400
#define DAC_CR ((volatile u32 *)(DAC + 0x00))
#define DAC_DHR12R1 ((volatile u32 *)(DAC + 0x08))
#define GPIOA_MODER (GPIOx_MODER(IO(PORTA, 0)))
#define GPIOA_PUPDR (GPIOx_PUPDR(IO(PORTA, 0)))
void dac_init()
{
    // Enable GPIOA clock
    or32(RCC_AHBENR, BIT17); // IOPAEN

    // Set PA4 to analog mode (MODER = 11)
    or32(GPIOA_MODER, (3U << (4 * 2))); // analog mode
    and32(GPIOA_PUPDR, ~(3U << (4 * 2))); // no pull-up/down

    // Enable DAC clock
    or32(RCC_APB1ENR, BIT29); // DACEN

    // Enable DAC channel 1 (DAC_OUT1)
    wr32(DAC_DHR12R1, 0); // data register
    or32(DAC_CR, BIT0); // EN1
    
    // Optional: Disable Output Buffer (lower drive, less noise)
    //or32(DAC_CR, BIT1); // BOFF1;
}

void dac_set(uint16_t value)
{
    // 12-bit right-aligned value (0–4095)
    if (value > 956) // 0.7V safety
      value = 956;
    wr32(DAC_DHR12R1, value & (1024-1)); // 0,75V safety
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

#define ADC 0x40012400
#define ADC_ISR    ((volatile u32 *)(ADC + 0x00))
#define ADC_CR     ((volatile u32 *)(ADC + 0x08))
#define ADC_CFGR2  ((volatile u32 *)(ADC + 0x10))
#define ADC_SMPR   ((volatile u32 *)(ADC + 0x14))
#define ADC_CHSELR ((volatile u32 *)(ADC + 0x28))
#define ADC_DR     ((volatile u32 *)(ADC + 0x40))
void adc_init()
{
    // measure ouput voltage with ADC_IN4 (also on PA4)

    // Enable GPIOA clock
    or32(RCC_AHBENR, BIT17); // IOPAEN

    // PA4 analog mode
    or32(GPIOA_MODER, (3U << (4 * 2))); // analog mode
    and32(GPIOA_PUPDR, ~(3U << (4 * 2))); // no pull-up/down

    // Enable ADC clock
    or32(RCC_APB2ENR, BIT9); // ADCEN
    /*
    or32(RCC_CR2, BIT0); // HSI14ON
    while ((rd32(RCC_CR2) & BIT1) == 0); // HSI14RDY
    */

    // Disable ADC if enabled
    if (rd32(ADC_CR) & BIT0) //ADEN
    {
        //printf("ADC turning off %x\n", rd32(ADC_CR));
        or32(ADC_CR, BIT1); // ADDIS
        while (rd32(ADC_CR) & BIT1); // ADDIS
    }
    //printf("ADC turned off\n");

    // ADC clock = ADCCLK
    and32(ADC_CFGR2, ~(BIT31 | BIT30)); // CKMODE

    // Select channel 4 (PA4)
    wr32(ADC_CHSELR, BIT4); // CHSEL4

    // Long sampling time (239.5 cycles)
    wr32(ADC_SMPR, 0x7); // SMP_0 | SMP_1 | SMP_2

    // Calibrate ADC (recommended)
    or32(ADC_CR, BIT31); // ADCAL
    while (rd32(ADC_CR) & BIT31); //ADCAL
    //printf("ADC calibrated\n");

    // Enable ADC
    or32(ADC_CR, BIT0); // ADEN
    while (!(rd32(ADC_ISR) & BIT0)); // ADRDY
    //printf("ADC enabled\n");
}

uint16_t adc_get()
{
    // Start conversion
    or32(ADC_CR, BIT2); // ADSTART

    // Wait for end of conversion
    while (!(rd32(ADC_ISR) & BIT2)); // EOC

    // Read result
    return (uint16_t)rd32(ADC_DR);
}

uint16_t adc_get_mv()
{
    uint32_t adc_val = adc_get();
    printf("adc raw: %d\n", adc_val);
    return adc_val * operating_voltage / 4095;
}

#define GPIOC_MODER (GPIOx_MODER(IO(PORTC, 0)))
#define GPIOC_OTYPER (GPIOx_OTYPER(IO(PORTC, 0)))
#define GPIOC_OSPEEDR (GPIOx_OSPEEDR(IO(PORTC, 0)))
#define GPIOC_PUPDR (GPIOx_PUPDR(IO(PORTC, 0)))
void exp_prog_gpio_sync_init() {
	// use PC12

	// Enable GPIOC clock
	or32(RCC_AHBENR, BIT19); // IOPCEN

	// PC12 - MODER12 = 01 (general purpose output)
	and32(GPIOC_MODER, ~(3U << (12 * 2)));
	or32(GPIOC_MODER, (1U << (12 * 2)));

	// OTYPER12 = 0 (push-pull)
	and32(GPIOC_OTYPER, ~(1U << 12));

	// OSPEEDR12 = 11 (high speed)
	or32(GPIOC_OSPEEDR, (3U << (12 * 2)));

	// PUPDR12 = 00 (no pull-up/down)
	and32(GPIOC_PUPDR, ~(3U << (12 * 2)));
}

#define GPIOC_BSRR (*(volatile uint32_t *)(0x48000800 + 0x18))
void exp_prog_gpio_sync() {
	__asm volatile(
		"    ldr  r0, =0x48000818\n"   // GPIOC_BSRR
		"    mov r1, #1\n"
		"    lsl r1, r1, #12\n"      // set PC12
		"    str  r1, [r0]\n"
		"    lsl r1, r1, #16\n"      // reset PC12
		"    str  r1, [r0]\n"
	: 
	: );
}

void exp_prog_register_pause() {
	__asm volatile(
		"_exp_prog_register_pause_repeat:\n"
		"    bl exp_prog_gpio_sync\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    mov r7, #0\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    mov r7, #0\n"
		"    sub r7, r7, #1\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    b _exp_prog_register_pause_repeat\n"
	: 
	: );
}

void exp_prog_compute_pause() {
	__asm volatile(
		"_exp_prog_compute_pause_repeat:\n"
		"    bl exp_prog_gpio_sync\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    mov r6, #0x85\n"
		"    mov r7, #0xa1\n"
		"    mov r5, r6\n"
		"    mul r5, r5, r7\n"
		"    add r5, r5, r6\n"
		"    add r5, r5, r7\n"
		"    lsl r4, r5, #0xb\n"
		"    mov r5, r6\n"
		"    mul r5, r5, r7\n"
		"    add r5, r5, r6\n"
		"    add r5, r5, r7\n"
		"    add r4, r4, r5\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    b _exp_prog_compute_pause_repeat\n"
	: 
	: );
}

void exp_prog_printf() {
	printf("starting exp_prog_printf:\n");
	const char fmt_str[] = "print this benchmark: %d\n";
	int print_val = 0xdeadbeef;
	__asm volatile(
		"    mov r4, %0\n"
		"    mov r5, %1\n"
		"_exp_prog_printf_repeat:\n"
		"    bl exp_prog_gpio_sync\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    mov r0, r4\n"
		"    mov r1, r5\n"
		"    bl printf\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    nop\n"
		"    b _exp_prog_printf_repeat\n"
	:
	: "r"((void*)fmt_str), "r"(print_val));
}

void exp_prog_AES() {
}

static void isr_reset(void)
{
	unsigned char *src, *dest;

	/* Load data to ram */
	src = &_sdata_flash;
	dest = &_sdata;
	while (dest != &_edata)
		*dest++ = *src++;

	/* Set bss section to 0 */
	dest = &_sbss;
	while (dest != &_ebss)
		*dest++ = 0;

	/* Enable HSE (8MHz external oscillator) */
	or32(RCC_CR, BIT16);
	while (!(rd32(RCC_CR) & BIT17));

	/* PLLMUL=6 f_PLL=48MHz */
	and32(RCC_CFGR, ~((0b1111 << 18) | (0b11 << 15) | BIT17));
	or32(RCC_CFGR, (0b0100 << 18) | (0b11 << 15));
	or32(RCC_CR, BIT24);
	while (!(rd32(RCC_CR) & BIT25));

	/* Configure flash, LATENCY=001 */
	while(rd32(R_FLASH_SR) & BIT0);
	wr32(R_FLASH_ACR, 0b001);

	#ifdef NO_FLASH_LATENCY
		wr32(R_FLASH_ACR, 0b000);
	#else
		/* Use PLL as system clock */
		or32(RCC_CFGR, 0b10);
		while (((rd32(RCC_CFGR) >> 2) & 0x3) != 0b10);
	#endif

	/* Enable clock on used AHB and APB peripherals */
	or32(RCC_APB2ENR, BIT14); /* USART1 */
	or32(RCC_AHBENR, BIT17); /* GPIOA */

	/* Init systicks */
	ticks = 0;
	wr32(R_SYST_RVR, HCLCK / SYSTICKS_FREQ);
	wr32(R_SYST_CVR, 0);
	wr32(R_SYST_CSR, BIT0 | BIT1 | BIT2);

	uart_init();
	
	printf("\n\nInit done!\n");
	dac_init();
	dac_set_mv(350);

	/*
	adc_init();
	uint16_t adc_value;
	adc_value = adc_get_mv();
	printf("adc_value: %d \n", adc_value);
	adc_value = adc_get_mv();
	printf("adc_value: %d \n", adc_value);
	*/
	
	exp_prog_gpio_sync_init();
	
	//exp_prog_register_pause();
	//exp_prog_compute_pause();
	exp_prog_printf();
	//exp_prog_AES();

	while (1);
	main();
}

static void isr_none(void)
{
	printf(__func__);
	while(1);
}

static void isr_nmi(void)
{
	printf(__func__);
	while(1);
}

static void isr_hf(void)
{
	printf(__func__);
	while(1);
}

static void isr_systick(void)
{
	ticks++;
}

uint32_t systicks(void)
{
	return ticks;
}

static const void *attr_sect("isrv_sys") _isrv_sys[] = {
	/* Cortex-M0 system interrupts */
	STACK_TOP,	/* Stack top */
	isr_reset,	/* Reset */
	isr_nmi,	/* NMI */
	isr_hf,	/* Hard Fault */
	0,			/* Reserved */
	0,			/* Reserved */
	0,			/* Reserved */
	0,			/* Reserved */
	0,			/* Reserved */
	0,			/* Reserved */
	0,			/* Reserved */
	isr_none,	/* SVCall */
	0,			/* Reserved */
	0,			/* Reserved */
	isr_none,	/* PendSV */
	isr_systick,	/* SysTick */
};

static const void *attr_sect("isrv_irq") _isrv_irq[] = {
	/* Peripheral interrupts */
	isr_none, /* WWDG */
	isr_none, /* PVD_VDDIO2 */
	isr_none, /* RTC */
	isr_none, /* FLASH */
	isr_none, /* RCC_CRS */
	isr_none, /* EXTI0_1 */
	isr_none, /* EXTI2_3 */
	isr_none, /* EXTI4_15 */
	isr_none, /* TSC */
	isr_none, /* DMA_CH1 */
	isr_none, /* DMA_CH2_3, DMA2_CH1_2 */
	isr_none, /* DMA_CH4_5_6_7, DMA2_CH3_4_5  */
	isr_none, /* ADC_COMP */
	isr_none, /* TIM1_BRK_UP_TRG_COM */
	isr_none, /* TIM1_CC */
	isr_none, /* TIM2 */
	isr_none, /* TIM3 */
	isr_none, /* TIM6_DAC */
	isr_none,  /* TIM7 */
	isr_none, /* TIM14 */
	isr_none, /* TIM15 */
	isr_none, /* TIM16 */
	isr_none, /* TIM17 */
	isr_none, /* I2C1 */
	isr_none, /* I2C2 */
	isr_none, /* SPI1 */
	isr_none, /* SPI2 */
	isr_none, /* USART1 */
	isr_none, /* USART2 */
	isr_none, /* USART_3_4_5_6_7_8 */
	isr_none, /* CEC_CAN */
	isr_none, /* USB */
};
