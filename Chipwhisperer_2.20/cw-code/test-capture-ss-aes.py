import chipwhisperer as cw
import cwhardware
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np


PLATFORM = "CW308_STM32F0"
fw_path = 'simpleserial-base-CW308_STM32F0.hex'

n_samples = 24000
n_traces = 5000

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
hw.scope.adc.decimate = 4
hw.scope.clock.adc_src = "clkgen_x1"
time.sleep(0.1)

print("Target clock freq:", hw.scope.clock.clkgen_freq)
print("Sampling rate:", hw.scope.clock.adc_rate)

hw.program_target(fw_path)


#
# CAPTURE
#

ktp = cw.ktp.Basic()

traces = np.zeros([n_traces, n_samples], dtype=np.float32)
plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
keys = np.zeros([n_traces, 16], dtype=np.uint8)

key, text = ktp.next()

#target.set_key(key)

print("Capturing traces...")

for i in tqdm(range(n_traces)):
    while True:
        ret = hw.capture(text, key)
        if ret is not None:
            break

    k = np.array(list(ret.key), dtype=np.uint8)
    c = np.array(list(ret.textout), dtype=np.uint8)
    p = np.array(list(ret.textin), dtype=np.uint8)
    t = np.array(list(ret.wave), dtype=np.float32)

    traces[i] = t
    plaintexts[i] = p
    ciphertexts[i] = c
    keys[i] = k
    
    key, text = ktp.next() 


#
# DISCONNECT
#

hw.disconnect()

np.save("data/traces.npy", traces)
np.save("data/keys.npy", keys)
np.save("data/plaintexts.npy", plaintexts)
np.save("data/ciphertexts.npy", ciphertexts)

plt.plot(np.average(traces, axis=0))

plt.show()
