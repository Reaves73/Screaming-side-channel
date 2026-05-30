import numpy as np
from scipy.signal import find_peaks

def match_filter_convolution(trace, n_width:int):
    kernel = np.r_[-np.ones(n_width), np.ones(n_width)]

    pad_width = n_width*2 # TODO: maybe n_width*1 is enough
    pad_mode  = 'mean'

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

def eval_match_filter_find_trigger_num_peaks_err(num_peaks):
    num_pos_peaks, num_neg_peaks = num_peaks
    return abs(num_pos_peaks - 2) + abs(num_neg_peaks - 1)

def match_filter_find_trigger(response, n_min_distance:int=None, debug=False):
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
        #distance=n_min_distance if trigger_proc_ver == 1 else None,
        height=positive_threshold
    )

    # Find negative peaks
    # invert signal so valleys become peaks
    neg_peaks, neg_props = find_peaks(
        -response,
        #distance=n_min_distance if trigger_proc_ver == 1 else None,
        height=-negative_threshold
    )

    num_peaks = len(pos_peaks), len(neg_peaks)
    if n_min_distance is not None:
        pos_peaks = remove_close_values(pos_peaks, n_min_distance)
        neg_peaks = remove_close_values(neg_peaks, n_min_distance)

    if debug:
        print("Positive peaks:", pos_peaks)
        print("Negative peaks:", neg_peaks)

    if eval_match_filter_find_trigger_num_peaks_err((len(pos_peaks), len(neg_peaks))) != 0:
        return None

    idx_trig_mid = neg_peaks[0]
    idx_trig_left = pos_peaks[0]
    idx_trig_right = pos_peaks[1]
    if not(idx_trig_left < idx_trig_mid < idx_trig_right):
        return None

    return (idx_trig_mid, (idx_trig_left, idx_trig_right), eval_match_filter_find_trigger_num_peaks_err(num_peaks))

def get_trigger_end(detected_trigger, n_permit_range, n_permit_diff, trig_delay_samples=None, fs=None, debug=False):
    (idx_trig_mid, (idx_trig_left, idx_trig_right), _) = detected_trigger

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

    samples_left_right_diff = abs(samples_left - samples_right)
    if not(samples_left_right_diff < n_permit_diff):
        if debug:
            print("not valid: n_permit_diff")
        return None

    return idx_trig_right + samples_right - (0 if trig_delay_samples is None else trig_delay_samples), samples_left_right_diff

def get_trigger_quality(detected_trigger, trig_end):
    _, _, num_peaks_err = detected_trigger
    _, samples_left_right_diff = trig_end
    return num_peaks_err, samples_left_right_diff
