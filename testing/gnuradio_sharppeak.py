#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../software/lib")

import cwhardware
import sharpwhisperer
from gnuradio_recorder import Recorder

import time
import datetime
import tempfile
import numpy as np
import matplotlib.pyplot as plt

cfg = sharpwhisperer.get_experiment_setup_config()
PLATFORM = sharpwhisperer.get_experiment_setup_config_PLATFORM(cfg)

FIRMWARE = "simpleserial-aes"

hw = cwhardware.CWHardware()
hw.connect(PLATFORM)

# Confiture scope
hw.scope.default_setup();
time.sleep(0.1)

dstr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
tracefile = f"{tempfile.gettempdir()}/traces_testing_{dstr}.npy"

sharpwhisperer.init_target(hw)
trace = None
try:
    sharpwhisperer.set_dac(hw.target, 0)
    sharpwhisperer.set_gate(hw.target, True)
    sharpwhisperer.init_sharppeak(hw.target, PLATFORM)
    with Recorder() as r:
        print(f"samprate={r.get_samprate()}")
        r.record_start(tracefile)
        time.sleep(0.01)
        sharpwhisperer.do_random_stuff(hw.target, 3)
        r.record_stop()
        trace = np.load(tracefile)
finally:
    sharpwhisperer.set_dac(hw.target, 0)
    sharpwhisperer.set_gate(hw.target, False)
    hw.disconnect()
    if os.path.exists(tracefile):
        os.remove(tracefile)

# now visualize the trace
if False:
    samples = np.fromfile(tracefile, dtype=np.float32)
    #print(samples[:30])
    #samples = np.clip(samples, -4, 4)
    samples = samples[100:]
    print(samples.shape)

    title = tracefile
    fs = 1/(5e6)
    t = np.arange(len(samples)) / fs

    plt.figure(figsize=(10, 4))
    plt.plot(t, samples)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    try:
        np.save(tracefile, np.stack([trace]))
        os.system(" ".join(["python3", os.path.dirname(os.path.realpath(__file__)) + "/../software/visualize.py", tracefile, "20"]))
    finally:
        if os.path.exists(tracefile):
            os.remove(tracefile)
