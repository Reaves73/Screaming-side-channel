#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpwhisperer
import sharpanalyzer

import numpy as np
import matplotlib.pyplot as plt
import argparse

sharpwhisperer.probe_usage_lock()


# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="path to traces file in experiment directory with plaintexts and keys")

parser.add_argument("-un", "--use_n_traces", help="only use the first n traces", type=int, default=None)

args = parser.parse_args()
tvla_params = {"use_n_traces": args.use_n_traces}

# load and prepare
# ---------------------------
expid, traces, plaintexts, keys = sharpanalyzer.load_traces(args.filepath, use_n_traces=tvla_params["use_n_traces"], expect_single_key=False)


# run
# ---------------------------
t_values = sharpanalyzer.run_tvla(traces, plaintexts, keys, output=True)
sharpanalyzer.find_t_mean_min_max(t_values, output=True)

sharpanalyzer.plot_tvla_trace(t_values, args.filepath, expid, tvla_params, save_plots=False)
