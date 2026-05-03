import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import cwhardware
import sharpwhisperer

import time

def main():
    hw = cwhardware.CWHardware()
    PLATFORM = "CW308_STM32F3"
    FIRMWARE = "simpleserial-aes"

    print("PLATFORM: ", PLATFORM)
    hw.connect(PLATFORM)

    # Confiture scope (so that target can run)
    hw.scope.default_setup()
    time.sleep(0.1)

    try:
        sharpwhisperer.init_target(hw)
    except:
        print("\ncould not initialize target")
        value = input("try programming it?").strip()
        if (value != "yes"):
            print("quitting.")
            return
        sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)

    def print_usage():
        print(
        """
    u      - set gate
    d      - set dac
    e      - get adc
    init   - run sharppeak init sequence
    r      - do some random stuff
    p      - program hex
    power  - control target power
    q      - quit
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
                print("- gate value must be 0 or 1.")
                continue

            resp = sharpwhisperer.set_gate(hw.target, value == "1")
            #print("gate reply:", )
            continue

        if cmd == "d":
            value = int(input("Which value? ").strip())
            if not 0 <= value <= 700:
                print("- bad value")
                continue

            resp = sharpwhisperer.set_dac(hw.target, int(value))
            #print("DAC reply:", resp[0])
            continue

        if cmd == "init":
            sharpwhisperer.init_sharppeak(hw.target)
            continue

        if cmd == "init1":
            sharpwhisperer.init_sharppeak(hw.target, i=1)
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
            sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)
            continue
    
        print("Unknown command.")
        print_usage()

    finally:
      sharpwhisperer.set_dac(hw.target, 0)
      sharpwhisperer.set_gate(hw.target, False)
      hw.disconnect()


if __name__ == "__main__":
    main()
