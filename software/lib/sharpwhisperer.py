import os
REPOPATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")

import time

def get_firmware(PLATFORM, FIRMWARE):
    # TODO: run compilation
    return f'{REPOPATH}/firmware/{FIRMWARE}/{FIRMWARE}-{PLATFORM}.hex'

# 1 - relay on, sharppeak connected;  0 - relay off, sharppeak diconnected
def set_relay(target, enabled):
    if enabled:
        target.simpleserial_write('u', bytearray([1]))
        #print(f"Relay set to 1.")
    else:
        target.simpleserial_write('u', bytearray([0]))
        #print(f"Relay set to 0.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def set_dac(target, value):
    assert 0 <= value <= 700
    payload = bytearray([(value >> 8) & 0xFF, value & 0xFF])
    target.simpleserial_write('d', payload)
    print(f"DAC set to {value}.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def get_adc(target):
    payload = bytearray([])
    target.simpleserial_write('e', payload)
    print(f"ADC value requested.")
    resp = target.simpleserial_read('g', 2)
    #print(resp)
    
    return int.from_bytes(resp, byteorder='big')

def do_random_stuff(target):
    payload = bytearray([])
    target.simpleserial_write('r', payload)
    print(f"doing random stuff requested.")
    resp = target.simpleserial_read('g', 1, timeout=10000) # timeout is in ms
    assert resp[0] == 1

def set_target_power(scope, on):
    scope.io.target_pwr = on

def reset_target(scope):
    set_target_power(scope, False)
    time.sleep(0.5)
    set_target_power(scope, True)
    time.sleep(0.5)