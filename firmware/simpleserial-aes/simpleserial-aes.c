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
#include "hal_extra.h"
#include "simpleserial.h"
#include <stdint.h>
#include <stdlib.h>

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

//buffer and len were given.
// set relay info and set.
uint8_t simpserial_set_relay(uint8_t* u, uint8_t len)
{
    //set relay state
    relay_set((uint8_t)(u[0]));
    uint8_t flag = 1;
    simpleserial_put('g', 1, &flag);
    return 0x00;
}

//set dac value and set.
uint8_t simpserial_set_dac(uint8_t* d, uint8_t len)
{
    //set dac value
    dac_set((uint16_t)(d[0] << 8 | d[1]));
    uint8_t flag = 1;
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
    
    // init relay
    relay_init();
    relay_set(0);// set relay off by default

    // init dac
    dac_init();
    dac_set(0);// set dac to 0 by default  

    //set dac output
    //delay_cycles(100000/1000);

    //dac_set(806); // 0.65V
    //dac_set(866); // 0.7V
    //delay_cycles(200000);

    //dac_set(372); // 0.3V
    //dac_set(434); // 0.35V
    //dac_set(559); // 0.45V
    //dac_set(496); //0.4 - 496
    //delay_cycles(20000);

    //switcher_set(1);
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
    simpleserial_addcmd('u', 1, simpserial_set_relay);
    simpleserial_addcmd('d', 2, simpserial_set_dac);
    #endif
    while(1)
        simpleserial_get();
}

