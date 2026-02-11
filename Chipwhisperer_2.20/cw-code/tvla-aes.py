import numpy as np
import matplotlib.pyplot as plt
from numpy.matlib import repmat
import sys
import scipy.stats as st
import aes

plaintexts_fname = "data/plaintexts.npy"
keys_fname = "data/keys.npy"
traces_fname = "data/traces.npy"


def hamming_weight(n):
    hw = 0
    while n != 0:
        if n % 2 == 1:
            hw += 1
        n >>= 1
    return hw

hamming_weight = np.vectorize(hamming_weight, signature="()->()")

HW_LUT_uint32 = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


# Return -1 for small HW, 1 for large HW, 0 for the middle HW
def hamming_weight_class(n) -> np.int8:
    max_hw = np.dtype(np.array(n).dtype).itemsize * 8
    if (max_hw % 2 == 0):
        mid_hw = max_hw // 2
    else:
        mid_hw = max_hw / 2
        
    hw = hamming_weight(n)
    if hw < mid_hw:
        return -1
    elif hw == mid_hw:
        return 0
    else:
        return 1

hamming_weight_class = np.vectorize(hamming_weight_class, signature="()->()")


def ttest(x, y):
    statistics, pvalue = st.ttest_ind(x, y, axis=0, equal_var=False)
    return statistics


def tvla(values, traces, f, pred_1, pred_2):
    mask = f(values)

    #idx_1 = np.nonzero(pred_1(mask))[0]
    #idx_2 = np.nonzero(pred_2(mask))[0]
    idx_1 = pred_1(mask)
    idx_2 = pred_2(mask)
    
    values_1 = values[idx_1]
    values_2 = values[idx_2]
    traces_1 = traces[idx_1]
    traces_2 = traces[idx_2]
    
    print("group 1 size:", values_1.size)
    print("group 2 size:", values_2.size)
    
    t_values = ttest(traces_1, traces_2)
    print("t_abs_max:", np.max(np.abs(t_values)))
    
    return t_values


#
# READ INPUTS
#

print("Reading inputs...")
plaintexts = np.load(plaintexts_fname)
keys = np.load(keys_fname)
traces = np.load(traces_fname)

assert(traces.shape[0] == plaintexts.shape[0])
assert(traces.shape[0] == keys.shape[0])
assert(len(traces.shape) == 2)
assert(len(plaintexts.shape) == 2)
assert(len(keys.shape) == 2)
assert(plaintexts.shape[1] == 16)
assert(keys.shape[1] == 16)
print("n_traces:", traces.shape[0])
print("n_samples:", traces.shape[-1])


N = None
if N is not None:
    traces = traces[:N]
    plaintexts = plaintexts[:N]
    keys = keys[:N]

labels = aes.get_first_sbox_output(plaintexts, keys)

#
# TVLA
#

# Wordwise followed by bytewise
t_values = np.zeros([16, traces.shape[-1]], dtype=np.float64)

for byte_idx in range(16):
    lab = labels[:,byte_idx]

    print(f"TVLA Byte {byte_idx}")
    t = tvla(lab, traces, hamming_weight_class, lambda x: x == -1, lambda x: x == 1)
    t_values[byte_idx] = t


plt.figure()
for b in range(16):
    plt.plot(t_values[b])

plt.show()

