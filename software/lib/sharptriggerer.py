import numpy as np
from scipy.signal import find_peaks

# 0 - old (stricter)
# 1 - new (remove close small peaks)
# 2 - update (remove close peaks from the left)
trigger_proc_ver = 2

def match_filter_convolution(trace, n_width):
    kernel = np.r_[-np.ones(n_width), np.ones(n_width)]

    pad_width = n_width if trigger_proc_ver == 0 else (n_width*2) # TODO: maybe n_width*1 is enough
    pad_mode = 'edge' if trigger_proc_ver == 0 else 'mean'

    # apply padding to avoid edge artifacts in response
    tracepad = np.pad(trace, pad_width, mode=pad_mode)
    response = np.convolve(tracepad, kernel, mode='same')

    return response[n_width:-n_width]

def remove_close_values(values, min_distance):
    if len(values) == 0:
        return []

    result = [values[0]]

    for v in values[1:]:
        if abs(v - result[-1]) >= min_distance:
            result.append(v)

    return result

def match_filter_find_trigger(response, n_min_distance=None, debug=False):
    if trigger_proc_ver == 0:
        n_min_distance = None
    # find trigger middle (negative response)
    edge_idx = np.argmin(response)
    edge_val = response[edge_idx]
    if not(edge_val < 0):
        return None
    edge_val = abs(edge_val)
    if debug:
        print("(edge_idx, edge_val) =", (edge_idx, edge_val))

    # find highest response (one of other two edges in trigger, positive response)
    edge_pos_idx = np.argmax(response)
    edge_pos_val = response[edge_pos_idx]
    if not(edge_pos_val >= 0 and edge_pos_val > edge_val / 3):
        return None
    if debug:
        print("(edge_pos_idx, edge_pos_val) =", (edge_pos_idx, edge_pos_val))

    positive_threshold = edge_pos_val / 3
    negative_threshold = -edge_val / 3

    # Find positive peaks
    pos_peaks, pos_props = find_peaks(
        response,
        distance=n_min_distance if trigger_proc_ver == 1 else None,
        height=positive_threshold
    )

    # Find negative peaks
    # invert signal so valleys become peaks
    neg_peaks, neg_props = find_peaks(
        -response,
        distance=n_min_distance if trigger_proc_ver == 1 else None,
        height=-negative_threshold
    )
    if trigger_proc_ver == 2:
        pos_peaks = remove_close_values(pos_peaks, n_min_distance)
        neg_peaks = remove_close_values(neg_peaks, n_min_distance)
    if debug:
        print("Positive peaks:", pos_peaks)
        print("Negative peaks:", neg_peaks)

    if not (len(pos_peaks) == 2 and len(neg_peaks) == 1):
        return None

    idx_trig_mid = neg_peaks[0]
    idx_trig_left = pos_peaks[0]
    idx_trig_right = pos_peaks[1]
    if not(idx_trig_left < idx_trig_mid < idx_trig_right):
        return None

    return (idx_trig_mid, (idx_trig_left, idx_trig_right))

def get_trigger_end(detected_trigger, n_permit_range, n_permit_diff, fs=None, debug=False):
    (idx_trig_mid, (idx_trig_left, idx_trig_right)) = detected_trigger

    samples_left  = (idx_trig_mid - idx_trig_left)
    samples_right = (idx_trig_right - idx_trig_mid)
    if debug and fs is not None:
        print("time_left:", samples_left / fs)
        print("time_right:", samples_right / fs)
        print("time_permit_range:", list(map(lambda x: x / fs, n_permit_range)))
        print("time_permit_diff:", n_permit_diff / fs)

    n_min, n_max = n_permit_range
    if not(all(map(lambda x: n_min <= x <= n_max, [samples_left, samples_right]))):
        if debug:
            print("not valid: n_permit_range")
        return None

    if not(abs(samples_left - samples_right) < n_permit_diff):
        if debug:
            print("not valid: n_permit_diff")
        return None
        

    return idx_trig_right + samples_right
