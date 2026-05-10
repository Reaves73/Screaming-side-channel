/*
    This file is part of the ChipWhisperer Example Targets
    Copyright (C) 2012-2017 NewAE Technology Inc.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "aes-independant.h"
#include "hal.h"
#include "simpleserial.h"
#include <stdint.h>
//#include <stdlib.h>

// our drivers
#include "dacadc.h"
#include "miscgpio.h"

uint8_t get_mask(uint8_t* m, uint8_t len)
{
  aes_indep_mask(m, len);
  return 0x00;
}

uint8_t get_key(uint8_t* k, uint8_t len)
{
	aes_indep_key(k);
	return 0x00;
}

uint8_t get_pt(uint8_t* pt, uint8_t len)
{
    aes_indep_enc_pretrigger(pt);

    dac_trigger();
	trigger_high();

  #ifdef ADD_JITTER
  for (volatile uint8_t k = 0; k < (*pt & 0x0F); k++);
  #endif

	aes_indep_enc(pt); /* encrypting the data block */
	trigger_low();

    aes_indep_enc_posttrigger(pt);

	simpleserial_put('r', 16, pt);
	return 0x00;
}

uint8_t reset(uint8_t* x, uint8_t len)
{
    // Reset key here if needed
	return 0x00;
}

static uint16_t num_encryption_rounds = 10;

uint8_t enc_multi_getpt(uint8_t* pt, uint8_t len)
{
    aes_indep_enc_pretrigger(pt);

    for(unsigned int i = 0; i < num_encryption_rounds; i++){
        dac_trigger();
        trigger_high();
        aes_indep_enc(pt);
        trigger_low();
    }

    aes_indep_enc_posttrigger(pt);
	simpleserial_put('r', 16, pt);
    return 0;
}

uint8_t enc_multi_setnum(uint8_t* t, uint8_t len)
{
    //Assumes user entered a number like [0, 200] to mean "200"
    //which is most sane looking for humans I think
    num_encryption_rounds = t[1];
    num_encryption_rounds |= t[0] << 8;
    return 0;
}

void gate_set(uint8_t on) {
    //set led state
    miscgpio_led_set(on);
    // set dac gate state
    dac_set_gate(on);
}


// set gate (and led)
uint8_t simpserial_set_gate(uint8_t* u, uint8_t len)
{
    gate_set(u[0]);
    uint8_t flag = 1;
    simpleserial_put('g', 1, &flag);
    return 0x00;
}

//set dac value and set.
uint8_t simpserial_set_dac(uint8_t* d, uint8_t len)
{
    //set dac value
    dac_set_mv((uint16_t)(d[0] << 8 | d[1]));
    uint8_t flag = 1;
    simpleserial_put('g', 1, &flag);
    return 0x00;
};

//get adc value.
uint8_t simpserial_get_adc(uint8_t* d, uint8_t len)
{
    uint16_t v = adc_get_mv();
    uint8_t data[2];
    data[0] = (uint8_t)((v >> 8) & 0xff);
    data[1] = (uint8_t)((v >> 0) & 0xff);
    simpleserial_put('g', 2, data);
    return 0x00;
};

//some computation
#include <stdio.h>
uint8_t simpserial_do_random_stuff(uint8_t* d, uint8_t len)
{
    uint8_t stuff_id = d[0];
    uint8_t flag = 1;

    char buffer[500];
    uint32_t* stp = (uint32_t*)(((uint32_t)buffer) & (~0x255));
    switch (stuff_id) {
        case 0:
            for (int i = 0; i < 10000; i++) {
                //sprintf(buffer, "hello random text %lu with %lu values %lu from memory", (uint32_t)(*(stp+0)), (uint32_t)(*(stp+10)), (uint32_t)(*(stp+30)));
            }
            break;
        case 1:
            delay_cycles(50000); // ~50ms delay
            break;
        case 2:
            dac_trigger();
            break;
        case 3:
            dac_trigger(); // 10ms +dv 10ms -dv 10ms 0dv 10ms
            delay_cycles(50000); // ~50ms delay
            dac_trigger(); // 10ms +dv 10ms -dv 10ms 0dv 10ms
            break;
        default:
            flag = 0;
            break;
    }

    simpleserial_put('g', 1, &flag);
    return 0x00;
};


#if SS_VER == SS_VER_2_1
uint8_t aes(uint8_t cmd, uint8_t scmd, uint8_t len, uint8_t *buf)
{
    uint8_t req_len = 0;
    uint8_t err = 0;
    uint8_t mask_len = 0;
    if (scmd & 0x04) {
        // Mask has variable length. First byte encodes the length
        mask_len = buf[req_len];
        req_len += 1 + mask_len;
        if (req_len > len) {
            return SS_ERR_LEN;
        }
        err = get_mask(buf + req_len - mask_len, mask_len);
        if (err)
            return err;
    }

    if (scmd & 0x02) {
        req_len += 16;
        if (req_len > len) {
            return SS_ERR_LEN;
        }
        err = get_key(buf + req_len - 16, 16);
        if (err)
            return err;
    }
    if (scmd & 0x01) {
        req_len += 16;
        if (req_len > len) {
            return SS_ERR_LEN;
        }
        err = get_pt(buf + req_len - 16, 16);
        if (err)
            return err;
    }

    if (len != req_len) {
        return SS_ERR_LEN;
    }

    return 0x00;

}
#endif

int main(void)
{
	uint8_t tmp[KEY_LENGTH] = {DEFAULT_KEY};

    platform_init();
    init_uart();
    trigger_setup();
    
    // init miscgpio
    miscgpio_init();

    // init dac and adc
    dacadc_init();
    dac_set(0);// set dac to 0 by default

    gate_set(0); // set gate off by default

    //while (1);
	aes_indep_init();
	aes_indep_key(tmp);

    /* Uncomment this to get a HELLO message for debug */

    // putch('h');
    // putch('e');
    // putch('l');
    // putch('l');
    // putch('o');
    // putch('\n');

	simpleserial_init();
    #if SS_VER == SS_VER_2_1
    simpleserial_addcmd(0x01, 16, aes);
    #else
    simpleserial_addcmd('k', 16, get_key);
    simpleserial_addcmd('p', 16,  get_pt);
    simpleserial_addcmd('x',  0,   reset);
    simpleserial_addcmd_flags('m', 18, get_mask, CMD_FLAG_LEN);
    simpleserial_addcmd('s', 2, enc_multi_setnum);
    simpleserial_addcmd('f', 16, enc_multi_getpt);
    simpleserial_addcmd('u', 1, simpserial_set_gate);
    simpleserial_addcmd('d', 2, simpserial_set_dac);
    simpleserial_addcmd('e', 0, simpserial_get_adc);
    simpleserial_addcmd('r', 1, simpserial_do_random_stuff);
    #endif
    while(1)
        simpleserial_get();
}

