#include <stdint.h>

void delay_cycles(volatile uint32_t count)
{
    while(count--) {
        __asm__("nop");
    }
}

