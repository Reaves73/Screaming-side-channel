#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpwhisperer
import sharpanalyzer

import numpy as np
import argparse

sharpwhisperer.probe_usage_lock()


# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="path to traces file in experiment directory with plaintexts and keys")

parser.add_argument("-un", "--use_n_traces", help="only use the first n traces", type=int, default=None)

args = parser.parse_args()

# load and prepare
# ---------------------------
expid, traces, plaintexts, key_full = sharpanalyzer.load_traces(args.filepath, use_n_traces=args.use_n_traces)
traces_z = sharpanalyzer.get_demeaned_zscore(traces)

# run
# ---------------------------
trace_counts, results = sharpanalyzer.run_ge_all_bytes(traces_z, plaintexts, key_full, n_trials=10, n_ge_samples=20)

sharpanalyzer.plot_pge_single(trace_counts, results, expid, save_plots=True)
