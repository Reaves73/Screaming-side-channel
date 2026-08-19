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


# load and prepare
# ---------------------------
_, traces, plaintexts, keys = sharpanalyzer.load_traces(args.filepath, use_n_traces=args.use_n_traces, expect_single_key=False)


# run
# ---------------------------
t_values = sharpanalyzer.run_tvla(traces, plaintexts, keys)
sharpanalyzer.find_t_mean_min_max(t_values)

plt.figure(figsize=(8, 5))
for b in range(16):
    plt.plot(t_values[b])
plt.axhline(0, color="black", linewidth=0.5)
plt.xlabel("Sample index")
plt.ylabel("t value")
#plt.title("Overall key recovery: mean vs worst-case byte")
#plt.legend()
plt.grid(True, alpha=0.3)
#plt.yscale("log")
plt.tight_layout()

plt.show()

