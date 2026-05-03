import os
REPOPATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")

import time

# ---------------------------

# enabled or disables DAC output
def set_gate(target, enabled):
    if enabled:
        target.simpleserial_write('u', bytearray([1]))
        #print(f"gate set to 1.")
    else:
        target.simpleserial_write('u', bytearray([0]))
        #print(f"gate set to 0.")
    print(f"Gate set to {'ENABLED' if enabled else 'DISABLED'}.")
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

def do_random_stuff(target, stuff_id):
    payload = bytearray([stuff_id & 0xFF])
    target.simpleserial_write('r', payload)
    print(f"doing random stuff {stuff_id} requested.")
    resp = target.simpleserial_read('g', 1, timeout=10000) # timeout is in ms
    if resp[0] != 1:
        print("random stuff failed")

# ---------------------------

def get_firmware(PLATFORM, FIRMWARE):
    return f'{REPOPATH}/firmware/{FIRMWARE}/{FIRMWARE}-{PLATFORM}.hex'

def set_target_power(scope, on):
    scope.io.target_pwr = on

def reset_target(scope):
    set_target_power(scope, False)
    time.sleep(0.5)
    set_target_power(scope, True)
    time.sleep(0.5)

def init_target(hw):
    reset_target(hw.scope)
    hw.target.flush()
    hw.reset_target()
    time.sleep(0.1)

    # test at the end
    resp = get_adc(hw.target)
    print("- ADC reply:", resp)

def program_target(PLATFORM, FIRMWARE, hw, compile=True):
    fw_path = get_firmware(PLATFORM, FIRMWARE)
    if compile:
        # run compilation
        res = os.system(f"{REPOPATH}/firmware/compile.sh")
        print(f"compilation result: {res}")
        assert res == 0
    reset_target(hw.scope)
    print("- progromming hex to target chip")
    print(f"- firmware: {fw_path}")
    hw.program_target(fw_path)

    # run an init at the end
    init_target(hw)

# ---------------------------

def init_sharppeak(target, i = 0):
    if i == 0:
        set_dac(target, 0)
        time.sleep(0.1)
        v = 700
        while v >= 350:
            set_dac(target, v)
            time.sleep(0.1)
            v -= 50

        resp = get_adc(target)
        print("- ADC value:", resp)
        return True

    elif i == 1:
        set_dac(target, 0)
        time.sleep(2)
        v = 700
        while v >= 400:
            set_dac(target, v)
            time.sleep(0.5)
            v -= 50

        resp = get_adc(target)
        print("- ADC value:", resp)
        return True

    raise Exception()
