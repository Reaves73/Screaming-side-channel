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
parser.add_argument("--plot_format_level", help="plot format type", type=int, default=0)
parser.add_argument("--plot_granularity_level", help="plot granularity level", type=int, default=0)

args = parser.parse_args()
analysis_params = sharpanalyzer.get_analysis_params(args.plot_granularity_level, args.plot_format_level)
analysis_params["use_n_traces"] = args.use_n_traces
analysis_params["use_logscale"] = False

tracefilepaths = args.filepaths.split(";")
labels = args.labels.split(";")
assert len(tracefilepaths) == len(labels)
print(f"number of experiments to process: {len(tracefilepaths)}")
print()

ge_list = []
for i in range(len(tracefilepaths)):
    tracefilepath = tracefilepaths[i]
    print(f"RUNNING {tracefilepath}")
    print("="*20)

    # load and prepare
    # ---------------------------
    _, traces, plaintexts, key_full = sharpanalyzer.load_traces(tracefilepath, use_n_traces=analysis_params["use_n_traces"], expect_single_key=True)
    traces_z = sharpanalyzer.get_demeaned_zscore(traces)

    # run
    # ---------------------------
    trace_counts, results = sharpanalyzer.run_ge_all_bytes(traces_z, plaintexts, key_full, n_trials=analysis_params["n_trials"], n_ge_samples=analysis_params["n_ge_samples"], use_logscale=analysis_params["use_logscale"])

    ge_list.append((labels[i], trace_counts, results))
    print()

sharpanalyzer.plot_pge_composition(ge_list, args.filepaths, analysis_params, save_plots=True, use_logscale=analysis_params["use_logscale"], plot_format=analysis_params["plot_format"])
