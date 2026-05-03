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


#yuqi_try
n_samples = 12000

n_traces = 5

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

hw.program_target(fw_path)


#
# CAPTURE
#

ktp = cw.ktp.Basic()

#traces = np.zeros([n_traces, n_samples], dtype=np.float32)
plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
keys = np.zeros([n_traces, 16], dtype=np.uint8)

key, text = ktp.next()

#target.set_key(key)

with Recorder() as r:
    print("Capturing traces...")

    tempdir = tempfile.gettempdir()
    for i in tqdm(range(n_traces)):
        tracefile = f"{tempdir}/traces_{i}.npy"
        while True:
            r.record_start(tracefile)
            ret = hw.capture(text, key)
            time.sleep(0.02)
            r.record_stop()

            if ret is not None:
                break
        k = np.array(list(ret.key), dtype=np.uint8)
        c = np.array(list(ret.textout), dtype=np.uint8)
        p = np.array(list(ret.textin), dtype=np.uint8)
        #t = np.array(list(ret.wave), dtype=np.float32)

        #t = np.array(ret.wave, dtype=np.float32)
        #tc = hw.scope.adc.trig_count
        #seg = t[int(tc/4): int(tc/4) + post_len]

        #traces[i] = t
        #traces[i, :len(seg)] = seg
        plaintexts[i] = p
        ciphertexts[i] = c
        keys[i] = k
        
        key, text = ktp.next() 


#
# DISCONNECT
#

hw.disconnect()

#np.save("data/traces.npy", traces)
np.save("data_sharppeak/keys.npy", keys)
np.save("data_sharppeak/plaintexts.npy", plaintexts)
np.save("data_sharppeak/ciphertexts.npy", ciphertexts)

#plt.plot(np.average(traces, axis=0))
#plt.plot(avg)
#yuqi_try: draw line of trigger.
#plt.axvline(x=0, color='red', linewidth=1)

plt.show()
