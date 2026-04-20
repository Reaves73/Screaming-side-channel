import chipwhisperer as cw
import cwhardware
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

# 1 - relay on, sharppeak connected;  0 - relay off, sharppeak diconnected
def set_relay(target, enabled):
    if enabled:
        target.simpleserial_write('u', bytearray([1]))
        print(f"Relay set to 1.")
    else:
        target.simpleserial_write('u', bytearray([0]))
        print(f"Relay set to 0.")
    resp = target.simpleserial_read('g', 1)
    return resp

def set_dac(target, value):
    payload = bytearray([(value >> 8) & 0xFF, value & 0xFF])
    target.simpleserial_write('d', payload)
    print(f"DAC set to {value}.")
    resp = target.simpleserial_read('g', 1)
    return resp



def main():
    hw = cwhardware.CWHardware()
    PLATFORM = "CW308_STM32F0"
    fw_path = '../../firmware/simpleserial-aes/simpleserial-aes-CW308_STM32F0.hex'

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

    print("\nintial relay state: off, dac value: 0\n")
    set_relay(hw.target, False)
    print("relay intialized!!!\n")
    set_dac(hw.target, 0)
    print("dac intialized!!!\n")
    print("give u to set relay, d to set dac, p to program hex, c to capture traces, q to quit")


    while True:
        cmd = input("dd> ").strip().lower()

        if cmd == "q":
            break

        if cmd == "u":
            value = input("0 or 1? ").strip()
            if value not in {"0", "1"}:
                print("Relay value must be 0 or 1.")
                continue

            resp = set_relay(hw.target, value == "1")#give true or false to set_relay
            print("Relay reply:", resp[0])
            continue

        if cmd == "d":
            value = int(input("Which value? ").strip())
            if not 0 <= value <= 1000:
                raise ValueError("error value")

            resp = set_dac(hw.target, int(value))
            print("DAC reply:", resp[0])
            continue

        if cmd == "p":
            print("progromming hex to target chip")
            hw.program_target(fw_path)
            continue

        if cmd == "c":
            print("Capturing trace...")
            # todo
    
            continue
    
        print("Unknown command. Use 'u', 'd', or 'q'.")
    
    hw.disconnect()



if __name__ == "__main__":
    main()
