import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import cwhardware
import sharpwhisperer

import chipwhisperer as cw
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np




def main():
    hw = cwhardware.CWHardware()
    PLATFORM = "CW308_STM32F3"
    FIRMWARE = "simpleserial-aes"
    fw_path = sharpwhisperer.get_firmware(PLATFORM, FIRMWARE)

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

    init_trial = 0
    while True:
        try:
            print("\nintial relay state: off, dac value: 0")
            sharpwhisperer.set_relay(hw.target, False)
            print("relay intialized!!!")
            sharpwhisperer.set_dac(hw.target, 0)
            print("dac intialized!!!")
            break
        except:
            print("\ncould not initialize board")
            init_trial += 1
            if init_trial == 1:
                print("trying to reset board")
                sharpwhisperer.reset_target(hw.scope)
            elif init_trial == 2:
                value = input("try programming it?").strip()
                if (value != "yes"):
                    print("quitting.")
                    return
                sharpwhisperer.reset_target(hw.scope)
                print("- progromming hex to target chip")
                print(f"- firmware: {fw_path}")
                hw.program_target(fw_path)
            else:
                print("nothing more to try, quitting.")
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
              sharpwhisperer.set_target_power(hw.scope, True)
            elif (value == "off"):
              sharpwhisperer.set_target_power(hw.scope, False)
            else:
              print("- you must write on or off")
            continue

        if cmd == "u":
            value = input("0 or 1? ").strip()
            if value not in {"0", "1"}:
                print("- Relay value must be 0 or 1.")
                continue

            resp = sharpwhisperer.set_relay(hw.target, value == "1")#give true or false to set_relay
            #print("Relay reply:", )
            continue

        if cmd == "d":
            value = int(input("Which value? ").strip())
            if not 0 <= value <= 700:
                print("- bad value")
                continue

            resp = sharpwhisperer.set_dac(hw.target, int(value))
            #print("DAC reply:", resp[0])
            continue

        if cmd == "init1":
            sharpwhisperer.set_dac(hw.target, 0)
            time.sleep(2)
            v = 700
            while v >= 400:
                sharpwhisperer.set_dac(hw.target, v)
                time.sleep(0.5)
                v -= 50

            resp = sharpwhisperer.get_adc(hw.target)
            print("- ADC value:", resp)
            continue

        if cmd == "init2":
            sharpwhisperer.set_dac(hw.target, 0)
            time.sleep(2)
            v = 700
            while v >= 350:
                sharpwhisperer.set_dac(hw.target, v)
                time.sleep(0.5)
                v -= 50

            resp = sharpwhisperer.get_adc(hw.target)
            print("- ADC value:", resp)
            continue

        if cmd == "e":
            resp = sharpwhisperer.get_adc(hw.target)
            print("- ADC reply:", resp)
            continue

        if cmd == "r":
            print("- doing random stuff")
            sharpwhisperer.do_random_stuff(hw.target)
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
      sharpwhisperer.set_dac(hw.target, 0)
      hw.disconnect()



if __name__ == "__main__":
    main()
