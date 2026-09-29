#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import numpy as np
import matplotlib.pyplot as plt

import sharpvisualizer

fs_cw = 7384615.384615385

filepath = "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_16-56-53_stm32f3_cwPWR_1000/traces_chipwhisperer.npy"
traces = np.load(filepath)
trace = traces.mean(axis=0)

#y *= -1


# plot
# ---------------------------
save_plots = False
s_idx_start = None
s_idx_end   = None
vis_params = {"metadata_filename": filepath, "expid": "2026-07-16_16-56-53_stm32f3_cwPWR_1000", "averaged_traces": -1, "s_idx_start": s_idx_start, "s_idx_end": s_idx_end}

def plotmodfun():
    #plt.axvline(2e-5, color="black", linewidth=1)
    plt.axvspan(2.07e-5, 4.11e-5, color='grey', alpha=0.3)

sharpvisualizer.plot_time(trace, fs=fs_cw, title=f"Power trace",
    pltmode=None, s_idx_start=s_idx_start, s_idx_end=s_idx_end, save_plots=save_plots, vis_params=vis_params, plotmodfun=plotmodfun, figsize=(6, 2))
sharpvisualizer.plot_fun()
