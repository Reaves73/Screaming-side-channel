#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpcapturer
import sharpvisualizer

import matplotlib.pyplot as plt
import numpy as np
import argparse

# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("experiment_name", help="short, concise name for the given experiment (will be part of experiment directory name)")

parser.add_argument("-d", "--duration_s", help="duration per trace in seconds (default: 2 ms)", type=float, default=2e-3)
parser.add_argument("-n", "--n_traces", help="number of traces (default: 1000)", type=int, default=1000)

parser.add_argument("--cw_adc_clkgen_x4", help="chipwhisperer adc_src set to clkgen_x4 (otherwise clkgen_x1)", action="store_true", default=False)
parser.add_argument("--cw_n_decimate", help="chipwhisperer decimate (default: 1)", type=int, default=1)

parser.add_argument("--exclude_gnuradio", help="disable gnuradio trace collection", action="store_true", default=False)

parser.add_argument("--visualize_trace_cw", help="for debugging. after capturing, visualize the first chipwhisperer trace", action="store_true", default=False)
parser.add_argument("--visualize_trace_gr", help="for debugging. after capturing, visualize the first gnuradio trace", action="store_true", default=False)

args = parser.parse_args()


# building the configuration dictionary
# ---------------------------
config_dict = {}
config_dict["experiment_name"] = args.experiment_name

config_dict["duration_s"] = args.duration_s
config_dict["n_traces"] = args.n_traces
#config_dict["n_traces"] = 5
#config_dict["n_traces"] = 50
#config_dict["n_traces"] = 5000

config_dict["include_trace_chipwhisperer"] = True
config_dict["include_trace_gnuradio"] = not args.exclude_gnuradio

#config_dict["chipwhisperer_n_samples"] = args.cw_n_samples
#config_dict["chipwhisperer_n_samples"] = 12000
#config_dict["chipwhisperer_n_samples"] = 24000

config_dict["chipwhisperer_adc_clkgen_x4"] = args.cw_adc_clkgen_x4
config_dict["chipwhisperer_n_decimate"] = args.cw_n_decimate
#config_dict["chipwhisperer_n_decimate"] = 1
#config_dict["chipwhisperer_n_decimate"] = 4

config_dict["gnuradio_samplerate"] = 5e6 # cannot be changed currently


# run the capturing function
# ---------------------------
cap_res = sharpcapturer.capture(config_dict)
if cap_res is None:
    print("capturing failed")
    sys.exit(-1)

experiment_dir, experiment_descr = cap_res
if args.visualize_trace_cw:
    sharpvisualizer.plot_time(np.load(f"{experiment_dir}/traces_chipwhisperer.npy")[0,:], experiment_descr["cw_adc_rate_measured"], title="first trace chipwhisperer")
if config_dict["include_trace_gnuradio"] and args.visualize_trace_gr:
    sharpvisualizer.plot_time(np.load(f"{experiment_dir}/traces_gnuradio.npy")[0,:], experiment_descr["gr_samplerate"], title="first trace gnuradio")


#plt.plot(np.average(traces, axis=0))
##plt.plot(avg)
##yuqi_try: draw line of trigger.
##plt.axvline(x=0, color='red', linewidth=1)
#
#plt.show()
