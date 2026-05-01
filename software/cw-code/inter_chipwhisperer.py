import chipwhisperer as cw
import cwhardware
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

import os
REPOPATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")

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

def main():
    hw = cwhardware.CWHardware()
    PLATFORM = "CW308_STM32F3"
    fw_path = f'{REPOPATH}/firmware/simpleserial-aes/simpleserial-aes-{PLATFORM}.hex'

    print("PLATFORM: ", PLATFORM)
    hw.connect(PLATFORM)

    n_samples = 12000
    n_traces = 5
    # Confiture scope
    hw.scope.default_setup()
    hw.reset_target()
    time.sleep(0.1)
    #hw.target.flush()
    hw.scope.adc.samples = n_samples
    hw.scope.adc.decimate = 1

    #hw.scope.adc.decimate = 4
    hw.scope.clock.adc_src = "clkgen_x1"
    time.sleep(0.1)

    print("Target clock freq:", hw.scope.clock.clkgen_freq)
    print("Sampling rate:", hw.scope.clock.adc_rate)

    try:
        print("\nintial relay state: off, dac value: 0\n")
        set_relay(hw.target, False)
        print("relay intialized!!!\n")
        set_dac(hw.target, 0)
        print("dac intialized!!!\n")
    except:
        print("could not initialize board")
        value = input("try programming it?").strip()
        if (value == "yes"):
            set_target_power(hw.scope, False)
            time.sleep(0.5)
            set_target_power(hw.scope, True)
            time.sleep(0.5)
            print("- progromming hex to target chip")
            print(f"- firmware: {fw_path}")
            hw.program_target(fw_path)
        else:
            print("quitting")
            return

    def print_usage():
        print(
        """
    u           - set relay
    d           - set dac
    e           - get adc
    init1/init2 - run sharppeak init sequence
    r           - do some random stuff
    p           - program hex
    c           - capture traces
    power       - control target power
    q           - quit
        """)
    print_usage()

    try:
      while True:
        cmd = input("dd> ").strip().lower()

        if cmd == "q":
            break

        if cmd == "power":
            value = input("turn on or off?").strip()
            if (value == "on"):
              set_target_power(hw.scope, True)
            elif (value == "off"):
              set_target_power(hw.scope, False)
            else:
              print("- you must write on or off")
            continue

        if cmd == "u":
            value = input("0 or 1? ").strip()
            if value not in {"0", "1"}:
                print("- Relay value must be 0 or 1.")
                continue

            resp = set_relay(hw.target, value == "1")#give true or false to set_relay
            #print("Relay reply:", )
            continue

        if cmd == "d":
            value = int(input("Which value? ").strip())
            if not 0 <= value <= 700:
                print("- bad value")
                continue

            resp = set_dac(hw.target, int(value))
            #print("DAC reply:", resp[0])
            continue

        if cmd == "init1":
            set_dac(hw.target, 0)
            time.sleep(2)
            v = 700
            while v >= 400:
                set_dac(hw.target, v)
                time.sleep(0.5)
                v -= 50

            resp = get_adc(hw.target)
            print("- ADC value:", resp)
            continue

        if cmd == "init2":
            set_dac(hw.target, 0)
            time.sleep(2)
            v = 700
            while v >= 350:
                set_dac(hw.target, v)
                time.sleep(0.5)
                v -= 50

            resp = get_adc(hw.target)
            print("- ADC value:", resp)
            continue

        if cmd == "e":
            resp = get_adc(hw.target)
            print("- ADC reply:", resp)
            continue

        if cmd == "r":
            print("- doing random stuff")
            do_random_stuff(hw.target)
            continue

        if cmd == "p":
            print("- progromming hex to target chip")
            print(f"- firmware: {fw_path}")
            hw.program_target(fw_path)
            continue

        if cmd == "c":
            print("- Capturing trace...")
            # todo
    
            continue
    
        print("Unknown command.")
        print_usage()

    finally:
      set_dac(hw.target, 0)
      hw.disconnect()



if __name__ == "__main__":
    main()
