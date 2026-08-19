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
_, traces, plaintexts, key_full = sharpanalyzer.load_traces(args.filepath, use_n_traces=args.use_n_traces, expect_single_key=True)
traces_z = sharpanalyzer.get_demeaned_zscore(traces)

# run
# ---------------------------
best_curves = sharpanalyzer.run_cpa_recovery(traces_z, plaintexts, key_full)

sharpanalyzer.plot_cpa_recovery(best_curves)
