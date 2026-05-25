#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../software/lib")

import sharpcapturer

import datetime
import tempfile
import numpy as np
import matplotlib.pyplot as plt

trace = sharpcapturer.sync_capture_random_stuff(3)

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
    dstr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tracefile = f"{tempfile.gettempdir()}/traces_testing_{dstr}.npy"
    try:
        np.save(tracefile, np.stack([trace]))
        os.system(" ".join(["python3", os.path.dirname(os.path.realpath(__file__)) + "/../software/visualize.py", tracefile, "--factor", "20"]))
    finally:
        if os.path.exists(tracefile):
            os.remove(tracefile)
