import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import decimate

import sharpwhisperer

def stream_downsample_average(trace, fs: float, duration_s: float, factor: int):
    total_samples = trace.size
    #total_samples = file_size // 4  # float32
    #samples_to_read = min(int(fs * duration_s), total_samples)
    samples_to_read = total_samples
    #print(f" {file_size} bytes")

    #print(f" {total_samples}")
    #print(f" {samples_to_read}")
    #print(f" {samples_to_read / fs:.6f} s")

    if factor <= 1:
        raise ValueError("require factor > 1")

    #averaged = []

    # TODO: use fs and duration_s; preserve averaging?
    trace_ds = decimate(trace, factor)
    #with open(path, "rb") as f:
    #    samples_done = 0
    #    while samples_done < samples_to_read:
    #        need = min(factor, samples_to_read - samples_done)
    #        chunk = np.fromfile(f, dtype=np.float32, count=need)
    #        # TODO: no idea why the first 100 samples of gnuradio are so weird, clipping is a quickfix
    #        chunk = np.clip(chunk, -4, 4)

    #        if len(chunk) == 0:
    #            break

    #        averaged.append(np.mean(chunk))
    #        samples_done += len(chunk)

    #y = np.array(averaged, dtype=np.float32)
    #fs_down = fs / factor
    #fs_ds = fs / factor
    fs_ds = None

    return trace_ds, fs_ds

def plot_fun(pltmode=True):
    if pltmode:
        plt.show()
    else:
        if not pltmode:
            plt.show(block=False)

def plot_clear_all():
    plt.close('all')

def plot_time(samples, fs=None, title="Time Domain", vlines=None, pltmode=True, s_idx_start=None, s_idx_end=None, save_plots=False, vis_params=None):
    lastidx = samples.shape[0] - 1
    if s_idx_start is None:
        s_idx_start = 0
    assert s_idx_start >= 0
    assert s_idx_start <= lastidx
    if s_idx_end is None:
        s_idx_end = lastidx
    assert s_idx_end >= 0
    assert s_idx_end <= lastidx

    savedplots_dir = None
    if save_plots:
        assert vis_params is not None
        savedplots_dir = sharpwhisperer.get_new_plots_dir(vis_params["expid"], "vis")
    
    if vis_params is not None:
        metadata_text = ""
        metadata_text += f"filename: {vis_params['metadata_filename']}\n"
        metadata_text += f"expid: {vis_params['expid']}\n"
        metadata_text += f"vis_params: {vis_params}\n"
        print("Plot metadata:")
        print("="*20)
        print(metadata_text)
        print()
        if savedplots_dir is not None:
            with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
                f.write(metadata_text)

    fs_v = fs
    if fs_v is None:
        fs_v = 1
    #fig, ax = plt.subplots()
    t = (np.arange(len(samples)) / fs_v)
    plt.figure(figsize=(8, 5))
    plt.plot(t[s_idx_start:s_idx_end], samples[s_idx_start:s_idx_end])
    #plt.title(title)
    plt.xlabel("Sample index" if fs is None else "Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if vlines is not None:
        for vline in vlines:
            plt.axvline(x=vline / fs_v, color='red', linestyle='--', linewidth=2)

    if savedplots_dir is None:
        plot_fun(pltmode)
    else:
        plt.savefig(f"{savedplots_dir}/trace.png", dpi=150)

def plot_spectrum(samples, fs, title="Spectrum", pltmode=True):
    n = min(len(samples), 65536)
    if n < 16:
        print("sample too less")
        return

    x = samples[:n] - np.mean(samples[:n])
    window = np.hanning(n)
    X = np.fft.rfft(x * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mag_db = 20 * np.log10(np.abs(X) + 1e-12)

    plt.figure(figsize=(10, 4))
    plt.plot(freqs, mag_db)
    plt.title(title)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.grid(True)
    plt.tight_layout()
    plot_fun(pltmode)
