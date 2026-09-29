#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

fs_cw = 7384615.384615385
fs_gr = 5000000.0

inputs = [
    ("PWR",                "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_16-56-53_stm32f3_cwPWR_1000/traces_chipwhisperer.npy",                   1,      0.2,       184, fs_cw),
    ("DACwLNA 350 noVDDA", "/sharpwhisperer_mirror/safe_2_paper/2026-06-12_20-35-44_stm32f3_cwDACwlna_vddarevert_500000/traces_chipwhisperer.npy", -25,     0.09,      184, fs_cw),
    ("DACwLNA 350",        "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_16-24-09_stm32f3_cwDACwlna_350mV_5000/traces_chipwhisperer.npy",        -2,      0.05-0.08, 184, fs_cw),
    ("DAC 350",            "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_15-45-36_stm32f3_cwDAC_350mV_10000/traces_chipwhisperer.npy",           -20,     0-0.08,    184, fs_cw),
    ("DAC 700",            "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_15-26-08_stm32f3_cwDAC_700mV_2000/traces_chipwhisperer.npy",            -20,     0-0.08,    184, fs_cw),
    ("SP",                 "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_13-26-25_sharppeak_1000_gain8/traces_gnuradio.npy",                      0.5/3, -0.07,      378, fs_gr),
    ("VCO",                "/sharpwhisperer_mirror/safe_2_paper/2026-07-16_11-26-39_vco_10000_30dbattenuator/traces_gnuradio.npy",                  0.5,   -0.15,      378, fs_gr),
]

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

# ----------------------------------------------------------------------
# Load all files
# ----------------------------------------------------------------------

traces_data = []

for label, filename, y_scale, y_off, cur_reference_x, cur_fs in inputs:
    traces = np.load(filename)

    (ts, traces) = extract_traces_ts(traces, cur_reference_x, cur_fs)

    trace = traces.mean(axis=0) * y_scale + y_off
    traces_data.append((label, ts, trace))



fig, ax = plt.subplots(figsize=(7, 4))
for (label, ts, trace) in traces_data:

    ax.plot(
        ts,
        trace,
        label=label,
    )

ax.set_xlabel("Time (s)")
ax.set_ylabel("Relative Amplitude")
plt.yticks([])

ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()
plt.show()