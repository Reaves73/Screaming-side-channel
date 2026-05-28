#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../software/lib")

import sharpcapturer
import sharptriggerer
import sharpvisualizer

import argparse
import numpy as np

# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filepath", help="path to traces file (must be uncut traces with trigger!!!)")
parser.add_argument("-n", "--n_traces", help="number of traces (default: 1)", type=int, default=1)
parser.add_argument("-fs", "--samprate", help="sampling rate (default: 5e6)", type=float, default=5e6)

args = parser.parse_args()

fs = args.samprate
if args.filepath is not None:
    traces = np.load(args.filepath)
    traces = traces[:args.n_traces,:]
else:
    traces = sharpcapturer.capture_random_stuff(2, numtraces=args.n_traces, fs=fs)
assert traces is not None

for trace_idx in range(traces.shape[0]):
    print(f"Trace {trace_idx}")
    print("="*20)
    trace = traces[trace_idx,:]

    sharpvisualizer.plot_time(trace, fs, title=f"original trace", pltmode=None)

    n_width = round(5e-3 * fs / 100)
    print("n_width:", n_width)
    response = sharptriggerer.match_filter_convolution(trace, n_width)

    sharpvisualizer.plot_time(response, fs, title=f"trigger edge response", pltmode=None)

    if sharptriggerer.match_filter_find_trigger(response, 1, debug=True) is None:
        print("trigger distance issue")

    detected_trigger = sharptriggerer.match_filter_find_trigger(response, n_width, debug=True)
    if detected_trigger is None:
        print("trigger not found")
        sharpvisualizer.plot_fun()
        assert False

    n_permit_range = (4e-3 * fs, 15e-3 * fs)
    n_permit_diff = 4e-7 * fs
    trig_end = sharptriggerer.get_trigger_end(detected_trigger, n_permit_range, n_permit_diff, fs=fs, debug=True)
    if trig_end is None:
        print("trigger signal not valid")
        sharpvisualizer.plot_fun()
        assert False

    idx_left_cutoff, _ = trig_end
    sharpvisualizer.plot_time(trace, fs, title=f"original trace with cutoff", vlines=[idx_left_cutoff], pltmode=None)

    if traces.shape[0] > 1:
        print("\n")
        sharpvisualizer.plot_clear_all()

sharpvisualizer.plot_fun()
