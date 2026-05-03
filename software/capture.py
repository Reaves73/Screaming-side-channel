import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import cwhardware
import sharpwhisperer
from gnuradio_recorder import Recorder

import chipwhisperer as cw
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import tempfile

#PLATFORM = "CW308_STM32F0"
PLATFORM = "CW308_STM32F3"
FIRMWARE = "simpleserial-aes"
fw_path = sharpwhisperer.get_firmware(PLATFORM, FIRMWARE)

CAPTURE_SOURCE = "CW"
#CAPTURE_SOURCE = "gnuradio"

#yuqi_try
n_samples = 12000
#n_samples = 24000

n_traces = 5
#n_traces = 50
#n_traces = 5000

print("PLATFORM: ", PLATFORM)
print("fw_path: ", fw_path)

#
# SETUP
#

hw = cwhardware.CWHardware()
hw.connect(PLATFORM)

# Confiture scope
hw.scope.default_setup();
hw.scope.adc.samples = n_samples

#yuqi_try
hw.scope.adc.decimate = 1

#hw.scope.adc.decimate = 4
hw.scope.clock.adc_src = "clkgen_x1"
time.sleep(0.1)

print("Target clock freq:", hw.scope.clock.clkgen_freq)
print("Sampling rate:", hw.scope.clock.adc_rate)

sharpwhisperer.init_target(hw)
#sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)


#
# CAPTURE
#

ktp = cw.ktp.Basic()

traces = None
if CAPTURE_SOURCE == "CW":
    traces = np.zeros([n_traces, n_samples], dtype=np.float32)

plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
keys = np.zeros([n_traces, 16], dtype=np.uint8)

key, text = ktp.next()

#target.set_key(key)

def capture_fun(cap_handle):
    global key, text
    print("Capturing traces...")

    if CAPTURE_SOURCE == "gnuradio":
        tempdir = tempfile.gettempdir()
    for i in tqdm(range(n_traces)):
        if CAPTURE_SOURCE == "gnuradio":
            tracefile = f"{tempdir}/traces_{i}.npy"
        while True:
            if CAPTURE_SOURCE == "gnuradio":
                cap_handle.record_start(tracefile)
            ret = hw.capture(text, key)
            if CAPTURE_SOURCE == "gnuradio":
                time.sleep(0.02)
                cap_handle.record_stop()

            if ret is not None:
                break
        k = np.array(list(ret.key), dtype=np.uint8)
        c = np.array(list(ret.textout), dtype=np.uint8)
        p = np.array(list(ret.textin), dtype=np.uint8)
        if CAPTURE_SOURCE == "CW":
            t = np.array(list(ret.wave), dtype=np.float32)
            #t = np.array(ret.wave, dtype=np.float32)
            #tc = hw.scope.adc.trig_count
            #seg = t[int(tc/4): int(tc/4) + post_len]

            #traces[i] = t
            #traces[i, :len(seg)] = seg
        plaintexts[i] = p
        ciphertexts[i] = c
        keys[i] = k
        
        key, text = ktp.next() 

if CAPTURE_SOURCE == "CW":
    capture_fun(None)
elif CAPTURE_SOURCE == "gnuradio":
    with Recorder() as r:
        capture_fun(r)

#
# DISCONNECT
#

hw.disconnect()

if CAPTURE_SOURCE == "CW":
    np.save("data/traces.npy", traces)
np.save("data_sharppeak/keys.npy", keys)
np.save("data_sharppeak/plaintexts.npy", plaintexts)
np.save("data_sharppeak/ciphertexts.npy", ciphertexts)

if CAPTURE_SOURCE == "CW":
    plt.plot(np.average(traces, axis=0))
    #plt.plot(avg)
    #yuqi_try: draw line of trigger.
    #plt.axvline(x=0, color='red', linewidth=1)

    plt.show()
