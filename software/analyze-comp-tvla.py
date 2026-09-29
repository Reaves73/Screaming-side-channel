#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpwhisperer
import sharpanalyzer

import numpy as np
import argparse

sharpwhisperer.probe_usage_lock()


fs_cw = 7384615.384615385
fs_gr = 5000000.0

reference_x = (184, 295)
reference_fs = fs_cw
add_left_right = (25+5, 7)
x_window_start = reference_x[0] - add_left_right[0]
x_window_stop  = reference_x[1] + add_left_right[1]

def extract_traces_ts(traces, cur_reference_x, cur_fs):
    # cut traces first for performance
    def translate_index(ref_index):
        cur_index = cur_reference_x + (ref_index - reference_x[0]) * (cur_fs / reference_fs)
        return cur_index
    x_start = round(translate_index(x_window_start) - 0.4)
    x_stop  = round(translate_index(x_window_stop)  + 0.4)+1
    traces = traces[:, x_start:x_stop]

    ts = np.arange(x_stop - x_start)/cur_fs + (x_window_start/fs_cw)
    return (ts, traces)


# parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("filepaths", help="path to traces files in experiment directory with plaintexts and keys (semicolon separated list)")
parser.add_argument("labels", help="labels of the data (semicolon separated list)")
parser.add_argument("use_n_tracess", help="only use the first n traces (semicolon separated list)")
parser.add_argument("capture_types", help="is it chipwhisperer (cw) or a gnuradio (gr) capture (semicolon separated list)")

parser.add_argument("byte_index", help="byte index to attack", type=int, default=0)

parser.add_argument("--plot_format_level", help="plot format type", type=int, default=2)

parser.add_argument("--save_plots", help="save the plots instead of showing them", action="store_true", default=False)

args = parser.parse_args()
analysis_params = {"plot_format": sharpanalyzer.get_plot_format_tuple(args.plot_format_level)}

tracefilepaths = args.filepaths.split(";")
labels = args.labels.split(";")
use_n_tracess = list(map(int, args.use_n_tracess.split(";")))
capture_types = args.capture_types.split(";")
assert len(tracefilepaths) == len(labels)
assert len(tracefilepaths) == len(use_n_tracess)
assert len(tracefilepaths) == len(capture_types)
print(f"number of experiments to process: {len(tracefilepaths)}")
print()

tvla_list = []
for i in range(len(tracefilepaths)):
    tracefilepath = tracefilepaths[i]
    use_n_traces = use_n_tracess[i]
    capture_type_cw = capture_types[i] == "cw"
    print(f"RUNNING {tracefilepath}")
    print("="*20)

    # load and prepare
    # ---------------------------
    _, traces, plaintexts, keys = sharpanalyzer.load_traces(tracefilepath, use_n_traces=use_n_traces, expect_single_key=False)
    cur_reference_x = 184 if capture_type_cw else 378
    cur_fs = fs_cw if capture_type_cw else fs_gr
    (ts, traces) = extract_traces_ts(traces, cur_reference_x, cur_fs)

    # run
    # ---------------------------
    t_values = sharpanalyzer.run_tvla(traces, plaintexts, keys, output=True, single_byte_index=args.byte_index)

    tvla_list.append((labels[i], t_values, ts))
    print()

sharpanalyzer.plot_tvla_trace_composition(tvla_list, args.filepaths, analysis_params, save_plots=args.save_plots, plot_format=analysis_params["plot_format"])
