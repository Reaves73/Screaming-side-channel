import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import decimate

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

def plot_time(samples, fs, title="Time Domain", vlines=None, pltmode=True):
    #fig, ax = plt.subplots()
    t = np.arange(len(samples)) / fs
    plt.figure(figsize=(10, 4))
    plt.plot(t, samples)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    if vlines is not None:
        for vline in vlines:
            plt.axvline(x=vline / fs, color='red', linestyle='--', linewidth=2)
    plot_fun(pltmode)

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
