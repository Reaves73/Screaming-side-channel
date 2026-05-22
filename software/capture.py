#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpcapturer

import matplotlib.pyplot as plt
import numpy as np
import argparse

# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("experiment_name", help="short, concise name for the given experiment (will be part of experiment directory name)")

parser.add_argument("-n", "--n_traces", help="number of traces (default: 1000)", type=int, default=1000)

parser.add_argument("--cw_n_samples", help="chipwhisperer samples (default: 12000)", type=int, default=12000)
parser.add_argument("--cw_n_decimate", help="chipwhisperer decimate (default: 1)", type=int, default=1)

parser.add_argument("--exclude_gnuradio", help="disable gnuradio trace collection", action="store_true", default=False)

args = parser.parse_args()


# building the configuration dictionary
# ---------------------------
config_dict = {}
config_dict["experiment_name"] = args.experiment_name

config_dict["n_traces"] = args.n_traces
#config_dict["n_traces"] = 5
#config_dict["n_traces"] = 50
#config_dict["n_traces"] = 5000

config_dict["include_trace_chipwhisperer"] = True
config_dict["include_trace_gnuradio"] = not args.exclude_gnuradio

config_dict["chipwhisperer_n_samples"] = args.cw_n_samples
#config_dict["chipwhisperer_n_samples"] = 12000
#config_dict["chipwhisperer_n_samples"] = 24000

config_dict["chipwhisperer_n_decimate"] = args.cw_n_decimate
#config_dict["chipwhisperer_n_decimate"] = 1
#config_dict["chipwhisperer_n_decimate"] = 4


# run the capturing function
# ---------------------------
sharpcapturer.capture(config_dict)


#plt.plot(np.average(traces, axis=0))
##plt.plot(avg)
##yuqi_try: draw line of trigger.
##plt.axvline(x=0, color='red', linewidth=1)
#
#plt.show()
