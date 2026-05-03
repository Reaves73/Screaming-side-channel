import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path


def stream_downsample_average(filepath: str, fs: float, duration_s: float, factor: int):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"file not exist: {filepath}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise ValueError("empty file")

    total_samples = file_size // 4  # float32
    samples_to_read = min(int(fs * duration_s), total_samples)

    print(f" {file_size} bytes")
    print(f" {total_samples}")
    print(f" {samples_to_read}")
    print(f" {samples_to_read / fs:.6f} s")

    if factor <= 1:
        raise ValueError("require factor > 1")

    averaged = []

    with open(path, "rb") as f:
        samples_done = 0
        while samples_done < samples_to_read:
            need = min(factor, samples_to_read - samples_done)
            chunk = np.fromfile(f, dtype=np.float32, count=need)
            # TODO: no idea why the first 100 samples of gnuradio are so weird, clipping is a quickfix
            chunk = np.clip(chunk, -4, 4)

            if len(chunk) == 0:
                break

            averaged.append(np.mean(chunk))
            samples_done += len(chunk)

    y = np.array(averaged, dtype=np.float32)
    fs_down = fs / factor

    return y, fs_down


def plot_time(samples, fs, title="Time Domain"):
    t = np.arange(len(samples)) / fs
    plt.figure(figsize=(10, 4))
    plt.plot(t, samples)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_spectrum(samples, fs, title="Spectrum"):
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
    plt.show()


def main():
    if len(sys.argv) < 5:
        print("invaild parameter")
        sys.exit(1)

    filepath = sys.argv[1]
    fs = float(sys.argv[2])
    duration_s = float(sys.argv[3])
    factor = int(sys.argv[4])

    y, fs_down = stream_downsample_average(filepath, fs, duration_s, factor)

    # 去直流
    y = y - np.mean(y)

    plot_time(y, fs_down, title=f"Downsampled Time Domain (factor={factor})")
    plot_spectrum(y, fs_down, title=f"Downsampled Spectrum (factor={factor})")


if __name__ == "__main__":
    main()