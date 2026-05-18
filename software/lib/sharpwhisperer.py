import os
REPOPATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")

import time
import datetime

# ---------------------------

def get_experiments_dir():
    experiments_dir_var = "SHARPWHISPERER_EXPERIMENTS"
    if experiments_dir_var not in os.environ:
        raise Exception(f"environment variable '{experiments_dir_var}' not defined")
    v = os.environ[experiments_dir_var]
    if not os.path.isdir(v):
        raise Exception(f"environment variable '{experiments_dir_var}' does not refer to existing directory '{v}'")
    return v

def get_new_experiment_dir(experiment_name):
    experiments_dir = get_experiments_dir()
    dstr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"{experiments_dir}/{dstr}_{experiment_name}"
    os.mkdir(path)
    return path

# ---------------------------

# enabled or disables DAC output
def set_gate(target, enabled):
    if enabled:
        target.simpleserial_write('u', bytearray([0, 1, 0]))
        #print(f"gate set to 1.")
    else:
        target.simpleserial_write('u', bytearray([0, 0, 0]))
        #print(f"gate set to 0.")
    print(f"Gate set to {'ENABLED' if enabled else 'DISABLED'}.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def set_dac(target, value):
    assert 0 <= value <= 700
    payload = bytearray([1, (value >> 8) & 0xFF, value & 0xFF])
    target.simpleserial_write('u', payload)
    print(f"DAC set to {value}.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def get_adc(target):
    payload = bytearray([2, 0, 0])
    target.simpleserial_write('u', payload)
    print(f"ADC value requested.")
    resp = target.simpleserial_read('g', 2)
    #print(resp)
    
    return int.from_bytes(resp, byteorder='big')

def do_random_stuff(target, stuff_id):
    payload = bytearray([3, stuff_id & 0xFF, 0])
    target.simpleserial_write('u', payload)
    print(f"doing random stuff {stuff_id} requested.")
    resp = target.simpleserial_read('g', 1, timeout=10000) # timeout is in ms
    if resp[0] != 1:
        print("random stuff failed")

def get_platform_id(target):
    target.simpleserial_write('u', bytearray([4, 0, 0]))
    resp = target.simpleserial_read('g', 1)
    assert resp[0] != 0
    if resp[0] == 1:
        return "CW308_STM32F0"
    elif resp[0] == 2:
        return "CW308_STM32F3"
    elif resp[0] == 3:
        return "CW308_STM32L4"
    else:
        return "UNKNOWN"

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
    target_platform = get_platform_id(hw.target)
    print(f"target replies as {target_platform}")
    return target_platform
    #resp = get_adc(hw.target)
    #print("- ADC reply:", resp)

def compile_firmware(PLATFORM, FIRMWARE):
    # run compilation
    res = os.system(f"{REPOPATH}/firmware/compile.sh {PLATFORM}")
    print(f"compilation result: {res}")
    return res

def program_target(PLATFORM, FIRMWARE, hw, compile=True):
    fw_path = get_firmware(PLATFORM, FIRMWARE)
    if compile:
        res = compile_firmware(PLATFORM, FIRMWARE)
        assert res == 0
    reset_target(hw.scope)
    print("- progromming hex to target chip")
    print(f"- firmware: {fw_path}")
    hw.program_target(fw_path)

    # run an init at the end
    target_platform = init_target(hw)
    if target_platform != PLATFORM:
        print(f"target reports unexpected id directly after programming: {target_platform}")
        assert False

# ---------------------------

def init_sharppeak(target, PLATFORM, i = 0):
    if i == 0:
        set_dac(target, 0)
        time.sleep(0.1)
        v = 700
        while v >= 350:
            set_dac(target, v)
            time.sleep(0.1)
            v -= 50
        if PLATFORM == "CW308_STM32F0":
            # 305 works with VDDA before shunt resistor
            set_dac(target, 324) # 324 works with VDDA and VDDA behind shunt resistor
            time.sleep(0.1)
        if PLATFORM == "CW308_STM32L4":
            set_dac(target, 320)
            time.sleep(0.1)
            set_dac(target, 290)
            time.sleep(0.1)
            set_dac(target, 271) # works with VDDA and VDDA behind shunt resistor
            time.sleep(0.1)
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
