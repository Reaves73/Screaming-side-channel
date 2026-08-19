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
pge_params = {"n_trials": 10, "n_ge_samples": 20}


# load and prepare
# ---------------------------
expid, traces, plaintexts, keys = sharpanalyzer.load_traces(args.filepath, use_n_traces=args.use_n_traces, expect_single_key=False)


# run
# ---------------------------
trace_counts, results = sharpanalyzer.run_ntvla(traces, plaintexts, keys, n_trials=pge_params["n_trials"], n_ge_samples=pge_params["n_ge_samples"])

sharpanalyzer.plot_ntvla_single(trace_counts, results, args.filepath, expid, pge_params, save_plots=True)
