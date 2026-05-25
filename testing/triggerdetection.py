#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../software/lib")

import sharptriggerer
import sharpvisualizer

import numpy as np
import argparse

# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="path to traces file (or single trace)")

args = parser.parse_args()


traces = np.load(args.filepath) # might be many traces actually
# only take the first trace if it is many traces
if len(traces.shape) > 1:
    trace = traces[0,:]
else:
    trace = traces

fs = 5e6
sharpvisualizer.plot_time(trace, fs, title=f"original trace")

n_width = int(5e-3 * fs / 100)
print("n_width:", n_width)
response = sharptriggerer.match_filter_convolution(trace, n_width)

sharpvisualizer.plot_time(response, fs, title=f"trigger edge response")

detected_trigger = sharptriggerer.match_filter_find_trigger(response, debug=True)
if detected_trigger is None:
    raise Exception("trigger not found")

n_permit_range = (4e-3 * fs, 15e-3 * fs)
n_permit_diff = 4e-7 * fs
idx_left_cutoff = sharptriggerer.get_trigger_end(detected_trigger, n_permit_range, n_permit_diff, fs=fs, debug=True)
if idx_left_cutoff is None:
    raise Exception("trigger signal not valid")

sharpvisualizer.plot_time(trace, fs, title=f"original trace with cutoff", vlines=[idx_left_cutoff])
