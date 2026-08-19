import numpy as np
from scipy.signal import correlate, butter, lfilter

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


def shift_trace(trace, shift):
    """
    Shift a 1D trace in time.
    Positive shift moves the trace to the right.
    Values shifted outside are filled with zeros.
    """
    n = len(trace)
    shifted = np.zeros_like(trace)

    if shift > 0:
        shifted[shift:] = trace[:-shift]
    elif shift < 0:
        shifted[:shift] = trace[-shift:]
    else:
        shifted[:] = trace

    return shifted


def best_shift(trace, prototype, max_shift=None):
    """
    Find the shift that maximizes correlation between trace and prototype.
    """
    corr = correlate(trace - np.mean(trace),
                     prototype - np.mean(prototype),
                     mode="full")

    lags = np.arange(-len(trace) + 1, len(trace))

    if max_shift is not None:
        mask = np.abs(lags) <= max_shift
        corr = corr[mask]
        lags = lags[mask]

    return lags[np.argmax(corr)]


def align_traces(traces, n_iter=10, max_shift=None, tol=1e-6):
    """
    Iteratively align traces to their mean prototype.

    Parameters
    ----------
    traces : ndarray
        Shape (n_traces, n_samples)
    n_iter : int
        Maximum number of alignment iterations.
    max_shift : int or None
        Maximum allowed time shift.
    tol : float
        Stop if prototype changes less than this.

    Returns
    -------
    aligned : ndarray
        Aligned traces.
    shifts : ndarray
        Estimated shifts for each trace.
    prototype : ndarray
        Final average trace.
    """

    traces = np.asarray(traces)

    # Initial prototype
    prototype = np.mean(traces, axis=0)

    shifts = np.zeros(len(traces), dtype=int)

    for iteration in range(n_iter):

        aligned = np.zeros_like(traces)

        # Align each trace to prototype
        for i, trace in enumerate(traces):
            shift = best_shift(trace, prototype, max_shift)
            shifts[i] = shift
            aligned[i] = shift_trace(trace, shift)

        # Update prototype
        new_prototype = np.mean(aligned, axis=0)

        # Check convergence
        change = np.linalg.norm(new_prototype - prototype)

        print(f"Iteration {iteration+1}: prototype change = {change:.3e}")

        prototype = new_prototype

        if change < tol:
            break

    return aligned, shifts, prototype

def misalign_traces(traces, max_shift, random_state=None):
    """
    Introduce random temporal misalignment to traces.

    Parameters
    ----------
    traces : ndarray
        Shape (n_traces, n_samples).
    max_shift : int
        Maximum absolute random shift (in samples).
        Each trace is shifted by a random value in
        [-max_shift, max_shift].
    random_state : int or None
        Seed for reproducibility.

    Returns
    -------
    misaligned : ndarray
        Copy of traces with random shifts applied.
    shifts : ndarray
        Applied shifts for each trace.
    """

    rng = np.random.default_rng(random_state)

    traces = np.asarray(traces)

    # Create a copy so the original data are untouched
    misaligned = np.zeros_like(traces)

    # Random shifts for each trace
    shifts = rng.integers(
        low=-max_shift,
        high=max_shift + 1,
        size=len(traces)
    )

    # Apply shifts
    for i, trace in enumerate(traces):
        misaligned[i] = shift_trace(trace, shifts[i])

    return misaligned, shifts

def trace_misalignment(traces, max_shift):
    misaligned, shifts = misalign_traces(traces, max_shift)
    print(shifts)
    print(shifts.shape)
    return misaligned

def align_traces_paper(traces_np,wstart=0,wend=0):
    traces = traces_np
    # align
    aligned = []
    target = None
    shifts = []
    for trace in traces:
        if target is None:
            target = trace
        else:
            shift = (np.argmax(correlate(trace, target)) - (len(target)-1))
            shifts.append(shift)
            if(shift >= 0):
                trace[0:len(trace)-shift-1] = trace[shift:len(trace)-1]
                trace[len(trace)-shift+1:len(trace)-1] = 0
            else:
                trace[0:len(trace)-1+shift] = trace[0:len(trace)-1+shift]
                trace[len(trace)+shift+1:len(trace)-1] = 0

        if(wstart!=wend):
            trace = trace[wstart:wend]

        # add your normalization code here
        # for example:
        # norm = np.average(trace)
        # if norm != 0:
        #     trace = trace / norm

        aligned.append(trace)

    print(np.asarray(shifts))
    return np.asarray(aligned)


def align_traces_paper2(traces_np, max_shift=None, template=None):
    traces = traces_np
    sampling_rate = 6000000.0
    aligned = []
    shifts = []
    for trace in traces:
        #trace = data[start:stop]
        if template is None:
            template = trace

        #trace_lpf = butter_lowpass_filter(trace, sampling_rate / 4, sampling_rate)
        #template_lpf = butter_lowpass_filter(template, sampling_rate / 4, sampling_rate)
        trace_lpf = trace
        template_lpf = template
        trace_lpf = trace_lpf - np.mean(trace_lpf)
        template_lpf = template_lpf - np.mean(template_lpf)
        
        correlation = correlate(trace_lpf**2, template_lpf**2)
        lags = np.arange(-len(trace) + 1, len(trace))
        if max_shift is not None:
            mask = np.abs(lags) <= max_shift
            correlation = correlation[mask]
            lags = lags[mask]
        #return lags[np.argmax(corr)]
        
        # print max(correlation)
        #if max(correlation) <= config.min_correlation:
        #    continue

        shift = np.argmax(correlation) - (len(template)-1)
        shift = lags[np.argmax(correlation)]
        shifts.append(shift)
        if(shift >= 0):
            trace[0:len(trace)-shift-1] = trace[shift:len(trace)-1]
            trace[len(trace)-shift+1:len(trace)-1] = 0
        else:
            trace[0:len(trace)-1+shift] = trace[0:len(trace)-1+shift]
            trace[len(trace)+shift+1:len(trace)-1] = 0
        #traces.append(data[start+shift:stop+shift])
        aligned.append(trace)

    shifts_np = np.asarray(shifts)
    print(shifts_np)
    print(shifts_np.shape)
    print(np.count_nonzero(shifts_np))

    aligned_np = np.asarray(aligned)
    template = np.average(aligned_np, axis=0)
    return aligned_np, template


def trace_alignment(traces, max_shift):
    #return traces
    #return align_traces_paper(traces)
    template = np.average(traces, axis=0)
    for _ in range(1):
        aligned_np, template = align_traces_paper2(traces, max_shift, template=template)
    return aligned_np
    aligned, shifts, prototype = align_traces(traces, max_shift=max_shift)
    print(shifts)
    return aligned
