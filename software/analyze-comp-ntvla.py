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
parser.add_argument("filepaths", help="path to traces files in experiment directory with plaintexts and keys (semicolon separated list)")
parser.add_argument("labels", help="labels of the data (semicolon separated list)")

parser.add_argument("-un", "--use_n_traces", help="only use the first n traces", type=int, default=None)

args = parser.parse_args()
ntvla_params = {"n_trials": 10, "n_ge_samples": 20, "use_n_traces": args.use_n_traces}

tracefilepaths = args.filepaths.split(";")
labels = args.labels.split(";")
assert len(tracefilepaths) == len(labels)
print(f"number of experiments to process: {len(tracefilepaths)}")
print()

ntvla_list = []
for i in range(len(tracefilepaths)):
    tracefilepath = tracefilepaths[i]
    print(f"RUNNING {tracefilepath}")
    print("="*20)

    # load and prepare
    # ---------------------------
    _, traces, plaintexts, keys = sharpanalyzer.load_traces(tracefilepath, use_n_traces=ntvla_params["use_n_traces"], expect_single_key=False)

    # run
    # ---------------------------
    trace_counts, results = sharpanalyzer.run_ntvla(traces, plaintexts, keys, n_trials=ntvla_params["n_trials"], n_ge_samples=ntvla_params["n_ge_samples"])

    ntvla_list.append((labels[i], trace_counts, results))
    print()

sharpanalyzer.plot_ntvla_composition(ntvla_list, args.filepaths, ntvla_params, save_plots=True)
