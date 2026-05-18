#include <stdint.h>

void delay_cycles(volatile uint32_t count)
{
#ifdef STM32F0
    count >>= 1;
#endif
    while(count--) {
        __asm__("nop");
    }
}
