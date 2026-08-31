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
parser.add_argument("--plot_format_level", help="plot format type", type=int, default=0)
parser.add_argument("--plot_granularity_level", help="plot granularity level", type=int, default=0)

args = parser.parse_args()
analysis_params = sharpanalyzer.get_analysis_params(args.plot_granularity_level, args.plot_format_level)
analysis_params["use_n_traces"] = args.use_n_traces


# load and prepare
# ---------------------------
expid, traces, plaintexts, keys = sharpanalyzer.load_traces(args.filepath, use_n_traces=analysis_params["use_n_traces"], expect_single_key=False)


# run
# ---------------------------
trace_counts, results = sharpanalyzer.run_ntvla(traces, plaintexts, keys, n_trials=analysis_params["n_trials"], n_ge_samples=analysis_params["n_ge_samples"])

sharpanalyzer.plot_ntvla_single(trace_counts, results, args.filepath, expid, analysis_params, save_plots=True, plot_format=analysis_params["plot_format"])
