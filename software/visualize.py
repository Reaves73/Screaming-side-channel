#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpvisualizer

import numpy as np
from pathlib import Path
import argparse

def main():
    # parse arguments
    # ---------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="path to traces file (or single trace)")

    parser.add_argument("--factor", help="decimation factor", type=int, default=1)
    
    parser.add_argument("--fs", help="sampling frequency", type=float, default=None)
    parser.add_argument("--duration", help="duration in seconds", type=float, default=None)

    parser.add_argument("--averaged_traces", help="how many traces to take and average", type=int, default=1)
    parser.add_argument("--sample_indexes", help="shows sample indexes instead of time at x axis", action="store_true", default=False)

    args = parser.parse_args()

    # process
    # ---------------------------
    path = Path(args.filepath)
    if not path.exists():
        raise FileNotFoundError(f"file not exist: {args.filepath}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise ValueError("empty file")

    traces = np.load(args.filepath) # might be many traces actually
    #print(trace.shape)
    # TODO: fix the case that our file only contains one trace
    #if len(trace.shape) > 1:
    #    trace = trace[0,:]
    #assert len(trace.shape) == 1
    #print(trace.shape)

    # don't have as many traces as we want to average (the subscription wouldn't break but nice to output for debugging and clarity)
    if traces.shape[0] < args.averaged_traces:
        print(traces.shape)
        raise Exception("not enough traces to average")
    traces = traces[:args.averaged_traces,:]
    trace = traces.mean(axis=0)

    # currently can't take fs and duration
    assert args.fs is None and args.duration is None
    fs = 500000

    if args.factor != 1:
        y, fs_down = sharpvisualizer.stream_downsample_average(trace, args.fs, args.duration, args.factor)
        fs_down = fs/args.factor
    else:
        y, fs_down = trace, args.fs

    # 去直流
    #y = y - np.mean(y)


    # plot
    # ---------------------------
    sharpvisualizer.plot_time(y, fs=(None if args.sample_indexes else fs), title=f"Downsampled Time Domain (factor={args.factor})", pltmode=None)
    sharpvisualizer.plot_spectrum(y, fs, title=f"Downsampled Spectrum (factor={args.factor})", pltmode=None)
    sharpvisualizer.plot_fun()


if __name__ == "__main__":
    main()