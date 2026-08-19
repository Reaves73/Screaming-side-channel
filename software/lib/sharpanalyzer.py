import numpy as np
from numpy.matlib import repmat
import scipy.stats as st
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import tqdm
import aes

import sharpaligner
import sharpwhisperer

# ====== AES SBOX ======
SBOX = np.array([
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
], dtype=np.uint8)

HW = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)

def cpa_byte(traces_z, pt_byte):

    N, S = traces_z.shape

    # generate matrix (256, N) for 256 key guess
    # hyp[g, i] = HW( SBOX(pt[i] ^ g) )
    x = pt_byte[None, :] ^ np.arange(256, dtype=np.uint8)[:, None]#for each byte of all plaintexts, arrange different key guess for it.
    hyp = HW[SBOX[x]].astype(np.float32)  # (256,N)

    hyp -= hyp.mean(axis=1, keepdims=True)
    hyp_std = hyp.std(axis=1, keepdims=True) + 1e-12
    hyp /= hyp_std

    # Pearson corr： corr[g, s] = (hyp[g,:] dot traces_z[:,s]) / (N-1)
    corr = (hyp @ traces_z) / (N - 1)   # (256,S)

    # find the most relevant guess
    abs_corr = np.abs(corr)
    g_best, s_best = np.unravel_index(np.argmax(abs_corr), abs_corr.shape)
    return int(g_best), float(abs_corr[g_best, s_best]), int(s_best), corr[g_best]

def cpa_byte_ge(traces_z, pt_byte):

    N, S = traces_z.shape

    # generate matrix (256, N) for 256 key guess
    # hyp[g, i] = HW( SBOX(pt[i] ^ g) )
    x = pt_byte[None, :] ^ np.arange(256, dtype=np.uint8)[:, None]#for each byte of all plaintexts, arrange different key guess for it.
    hyp = HW[SBOX[x]].astype(np.float32)  # (256,N)

    hyp -= hyp.mean(axis=1, keepdims=True)
    hyp_std = hyp.std(axis=1, keepdims=True) + 1e-12
    hyp /= hyp_std

    # Pearson corr： corr[g, s] = (hyp[g,:] dot traces_z[:,s]) / (N-1)
    corr = (hyp @ traces_z) / (N - 1)   # (256,S)

    # find the most relevant guess
    abs_corr = np.abs(corr)
    #g_best, s_best = np.unravel_index(np.argmax(abs_corr), abs_corr.shape)
    #return int(g_best), float(abs_corr[g_best, s_best]), int(s_best), corr[g_best]
    best_per_guess = abs_corr.max(axis=1)          # (256,)
    best_s_per_guess = abs_corr.argmax(axis=1)      # (256,) sample index for each guess

    g_best = int(np.argmax(best_per_guess))
    s_best = int(best_s_per_guess[g_best])

    return {
        "scores": best_per_guess,        # (256,) -> what you rank for PGE
        "corr_matrix": corr,             # (256,S) keep if you want full traceability
        "g_best": g_best,
        "s_best": s_best,
        "max_corr": float(best_per_guess[g_best]),
    }

def key_rank(scores, correct_key):
    # descending order rank of the correct key (0 = best guess)
    order = np.argsort(-scores)
    rank = int(np.where(order == correct_key)[0][0])
    return rank

def guessing_entropy(traces_z, pt_byte, correct_key, n_trials, trace_counts):
    """
    n_trials: number of repeated experiments per trace count (random trace subsets)
    trace_counts: list of N values to evaluate PGE at
    """
    ge_curve = []
    for N in trace_counts:
        ranks = []
        for _ in range(n_trials):
            idx = np.random.choice(traces_z.shape[0], N, replace=False)
            res = cpa_byte_ge(traces_z[idx], pt_byte[idx])
            ranks.append(key_rank(res["scores"], correct_key))
        ge_curve.append(np.mean(ranks))
    return np.array(ge_curve)

def load_traces(filepath, use_n_traces=None, expect_single_key=False):
    # process path
    # ---------------------------
    fpath = Path(filepath)
    if not fpath.exists():
        raise FileNotFoundError(f"path not exist: {filepath}")
    if not fpath.is_file():
        raise NotADirectoryError(f"path is not a file: {filepath}")

    traces_f = fpath
    path = fpath.parent
    expid = path.name
    pts_f = path / "plaintexts.npy"
    keys_f = path / "keys.npy"

    for f in [traces_f, pts_f, keys_f]:
        if not f.exists():
            raise FileNotFoundError(f"file not exist: {f}")
        if f.stat().st_size == 0:
            raise ValueError(f"empty file: {f}")

    print("Loading data...")
    traces = np.load(traces_f).astype(np.float32)
    pts    = np.load(pts_f).astype(np.uint8)
    keys   = np.load(keys_f).astype(np.uint8)

    #traces = sharpaligner.trace_misalignment(traces, 1)
    #traces = sharpaligner.trace_alignment(traces, 5)

    # as requested
    if use_n_traces is not None:
        print("Reducing number of traces...")
        traces = traces[:use_n_traces]
        pts    = pts[:use_n_traces]
        keys   = keys[:use_n_traces]
        
    N, S = traces.shape
    print(f"N traces: {N}, S samples: {S}")

    # if all keys are supposed to be the same
    if expect_single_key:
        if keys.ndim == 2:
            assert np.all(keys == keys[0]), "keys vary per trace — fixed-key assumption broken"
            keys = keys[0]
        #else:
        #    key_full = keys   # already (16,)

    return expid, traces, pts, keys

def get_demeaned_zscore(traces):
    # De-mean and z-score
    traces = traces - traces.mean(axis=0, keepdims=True)
    traces_std = traces.std(axis=0, keepdims=True) + 1e-12
    traces_z = traces / traces_std
    return traces_z

def run_cpa_recovery(traces_z, pts, true_key):
    recovered = np.zeros(16, dtype=np.uint8)
    best_curves = []

    for b in range(16):
        g, score, s_best, curve = cpa_byte(traces_z, pts[:, b])
        recovered[b] = g
        best_curves.append((b, curve, s_best, score))
        if true_key is not None:
            print(f"byte {b:02d}: guess=0x{g:02x}  highest={score:.4f}  at sample={s_best}  true=0x{true_key[b]:02x}")
        else:
            print(f"byte {b:02d}: guess=0x{g:02x}  highest={score:.4f}  at sample={s_best}")

    print("\nRecovered key:", recovered.tolist())
    if true_key is not None:
        print("True key:", true_key.tolist())
        print("Match bytes:", int(np.sum(recovered == true_key)), "/ 16")
    return best_curves

def plot_cpa_recovery(best_curves):
    plt.figure()
    for (b, curve, s_best, score) in best_curves[:8]:  # draw the first 8 bytes
        plt.plot(np.abs(curve), label=f"b{b} best@{s_best} ({score:.3f})")
    plt.title(" Correlation curves")
    plt.xlabel("sample index")
    plt.ylabel(" Correlation")
    plt.legend()
    plt.show()

def run_ge_all_bytes(traces_z, plaintexts, key_full, n_trials=50, trace_counts=None, n_ge_samples=20):
    if trace_counts is None:
        trace_counts = np.unique(np.linspace(10, traces_z.shape[0], n_ge_samples, dtype=int))
        #print(len(trace_counts))

    results = {}
    for b in tqdm(range(16)):
        pt_byte = plaintexts[:, b].astype(np.uint8)
        correct_key = int(key_full[b])
        ge_curve = guessing_entropy(traces_z, pt_byte, correct_key, n_trials, trace_counts)
        results[b] = ge_curve
        print(f"byte {b:2d} done — GE at max N: {ge_curve[-1]:.2f}")

    return trace_counts, results  # results[b] -> (len(trace_counts),) array

def find_minnumtraces_where_entropy0(trace_counts, results):
    ge_matrix = np.stack([results[b] for b in range(16)], axis=0)  # (16, len(trace_counts))
    all_zero = np.all(ge_matrix == 0, axis=0)                       # (len(trace_counts),) bool

    # find smallest index where all_zero is True from there to the end
    idx = np.where(all_zero[::-1] == False)[0]
    first_idx = len(all_zero) - idx[0] if len(idx) > 0 else 0

    if all_zero[first_idx:].all() and first_idx < trace_counts.shape[0]:
        n_traces_needed = trace_counts[first_idx]
        print(f"index {first_idx}, N={n_traces_needed}")
        return n_traces_needed
    else:
        print("never fully converges in this range")
        return None

def plot_pge_single(trace_counts, results, metadata_filename, expid, pge_params, save_plots=False):
    savedplots_dir = None
    if save_plots:
        savedplots_dir = sharpwhisperer.get_new_plots_dir(expid)
    
    minnumtraces = find_minnumtraces_where_entropy0(trace_counts, results)
    metadata_text = ""
    metadata_text += f"filename: {metadata_filename}\n"
    metadata_text += f"expid: {expid}\n"
    metadata_text += f"pge_params: {pge_params}\n"
    metadata_text += f"minnumtraces: {minnumtraces}\n"
    print("Plot metadata:")
    print("="*20)
    print(metadata_text)
    print()
    if savedplots_dir is not None:
        with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
            f.write(metadata_text)

    # ====== plotting code for the output of run_ge_all_bytes
    # --- all 16 bytes on one plot ---
    plt.figure(figsize=(10, 6))
    for b in range(16):
        plt.plot(trace_counts, results[b], label=f"byte {b}", alpha=0.7)

    plt.xlabel("Number of traces")
    plt.ylabel("Partial Guessing Entropy")
    #plt.title("Partial Guessing Entropy per key byte")
    #plt.legend(ncol=4, fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.axhline(0, color="black", linewidth=0.5)
    #plt.yscale("log")
    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/ge_per_byte.png", dpi=150)

    # ====== average GE across all bytes (a common way to report "how many traces to break the full key" at a glance):
    ge_matrix = np.stack([results[b] for b in range(16)], axis=0)  # (16, len(trace_counts))
    mean_ge = ge_matrix.mean(axis=0)
    worst_ge = ge_matrix.max(axis=0)   # hardest byte at each N — often more informative

    plt.figure(figsize=(8, 5))
    line, = plt.plot(trace_counts, mean_ge, label="mean", linewidth=2)
    plt.plot(trace_counts, worst_ge, label="max", linestyle="--", linewidth=2, color=line.get_color())
    plt.axhline(0, color="black", linewidth=0.5)
    plt.xlabel("Number of traces")
    plt.ylabel("Partial Guessing Entropy")
    #plt.title("Overall key recovery: mean vs worst-case byte")
    plt.legend()
    plt.grid(True, alpha=0.3)
    #plt.yscale("log")
    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/ge_summary.png", dpi=150)

def plot_pge_composition(ge_list, metadata_filenames, pge_params, save_plots=False):
    savedplots_dir = None
    if save_plots:
        savedplots_dir = sharpwhisperer.get_new_plots_dir("comp_pge")
    
    metadata_text = ""
    metadata_text += f"filenames: {metadata_filenames}\n"
    metadata_text += f"pge_params: {pge_params}\n"
    metadata_text += "-" * 20
    metadata_text += "\n"
    for label, tc, res in ge_list:
        minnumtraces = find_minnumtraces_where_entropy0(tc, res)
        metadata_text += f"label {label}\n"
        metadata_text += f"minnumtraces: {minnumtraces}\n"
        metadata_text += "\n"
    print("Plot metadata:")
    print("="*20)
    print(metadata_text)
    print()
    if savedplots_dir is not None:
        with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
            f.write(metadata_text)

    # ====== average GE across all bytes (a common way to report "how many traces to break the full key" at a glance):
    plt.figure(figsize=(8, 5))
    for label, tc, res in ge_list:
        ge_matrix = np.stack([res[b] for b in range(16)], axis=0)
        mean_ge = ge_matrix.mean(axis=0)
        worst_ge = ge_matrix.max(axis=0)

        line, = plt.plot(tc, mean_ge, linewidth=2, label=label)
        plt.plot(tc, worst_ge, linestyle="--", linewidth=2, color=line.get_color())

    plt.axhline(0, color="black", linewidth=0.5)
    plt.xlabel("Number of traces")
    plt.ylabel("Partial Guessing Entropy")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/ge_summary_comp.png", dpi=150)

# -------------------------------------------------------

def run_tvla(traces, plaintexts, keys, output=False):
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
        
        #print("group 1 size:", values_1.size)
        #print("group 2 size:", values_2.size)
        
        t_values = ttest(traces_1, traces_2)
        
        return t_values

    assert(traces.shape[0] == plaintexts.shape[0])
    assert(traces.shape[0] == keys.shape[0])
    assert(len(traces.shape) == 2)
    assert(len(plaintexts.shape) == 2)
    assert(len(keys.shape) == 2)
    assert(plaintexts.shape[1] == 16)
    assert(keys.shape[1] == 16)
    if output:
        print("n_traces:", traces.shape[0])
        print("n_samples:", traces.shape[-1])


    labels = aes.get_first_sbox_output(plaintexts, keys)

    #
    # TVLA
    #

    # Wordwise followed by bytewise
    t_values = np.zeros([16, traces.shape[-1]], dtype=np.float64)

    for byte_idx in range(16):
        lab = labels[:,byte_idx]

        t = tvla(lab, traces, hamming_weight_class, lambda x: x == -1, lambda x: x == 1)
        if output:
            print(f"TVLA Byte {byte_idx}")
            print("t_abs_max:", np.max(np.abs(t)))
        t_values[byte_idx] = t

    return t_values

def find_t_mean_min_max(t_values, output=False):
    t_abs_max = np.max(np.abs(t_values), axis=1)
    t_max_mean = t_abs_max.mean()
    t_max_min = t_abs_max.min()
    t_max_max = t_abs_max.max()
    if output:
        print()
        print(f"t_abs_max: mean={t_max_mean:.4f} (min={t_max_min:.4f}, max={t_max_max:.4f})")
    return (t_max_mean, t_max_min, t_max_max)

def run_ntvla(traces, plaintexts, keys, n_trials=10, trace_counts=None, n_ge_samples=20):
    if trace_counts is None:
        trace_counts = np.unique(np.linspace(10, traces.shape[0], n_ge_samples, dtype=int))
        #print(len(trace_counts))

    results =[]
    for N in tqdm(trace_counts):
        t_max_tuples = []
        for _ in range(n_trials):
            idx = np.random.choice(traces.shape[0], N, replace=False)
            t_values = run_tvla(traces[idx], plaintexts[idx], keys[idx])
            t_max_vals = find_t_mean_min_max(t_values)
            t_max_tuples.append(t_max_vals)
        len(t_max_tuples)
        results.append(np.mean(t_max_tuples, axis=0))
        #print(results[len(results) - 1].shape)

    return trace_counts, np.array(results)

def plot_tvla_trace(t_values, metadata_filename, expid, tvla_params, save_plots=False):
    savedplots_dir = None
    if save_plots:
        savedplots_dir = sharpwhisperer.get_new_plots_dir(expid)
    
    metadata_text = ""
    metadata_text += f"filename: {metadata_filename}\n"
    metadata_text += f"expid: {expid}\n"
    metadata_text += f"tvla_params: {tvla_params}\n"
    print("Plot metadata:")
    print("="*20)
    print(metadata_text)
    print()
    if savedplots_dir is not None:
        with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
            f.write(metadata_text)

    # ====== plotting code
    plt.figure(figsize=(8, 5))
    for b in range(16):
        plt.plot(t_values[b])
    plt.axhline(0, color="black", linewidth=0.5)
    plt.xlabel("Sample index")
    plt.ylabel("t value")
    #plt.title("Overall key recovery: mean vs worst-case byte")
    #plt.legend()
    plt.grid(True, alpha=0.3)
    #plt.yscale("log")
    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/tvla.png", dpi=150)

def plot_ntvla_single(trace_counts, results, metadata_filename, expid, ntvla_params, save_plots=False):
    savedplots_dir = None
    if save_plots:
        savedplots_dir = sharpwhisperer.get_new_plots_dir(expid)
    
    metadata_text = ""
    metadata_text += f"filename: {metadata_filename}\n"
    metadata_text += f"expid: {expid}\n"
    metadata_text += f"ntvla_params: {ntvla_params}\n"
    print("Plot metadata:")
    print("="*20)
    print(metadata_text)
    print()
    if savedplots_dir is not None:
        with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
            f.write(metadata_text)

    # ====== plotting code
    assert results.shape == (trace_counts.shape[0], 3)
    mean = results[:, 0]
    min_vals = results[:, 1]
    max_vals = results[:, 2]

    fig, ax = plt.subplots(figsize=(8, 5))

    color = 'tab:blue'

    # Shaded band between min and max
    ax.fill_between(trace_counts, min_vals, max_vals, color=color, alpha=0.2, label='Min–Max')

    # Optional: thin lines tracing the min and max edges
    ax.plot(trace_counts, min_vals, color=color, alpha=0.4, linewidth=1)
    ax.plot(trace_counts, max_vals, color=color, alpha=0.4, linewidth=1)

    # Mean line
    ax.plot(trace_counts, mean, color=color, linewidth=2, label='Mean')

    ax.set_xlabel('Number of traces')
    ax.set_ylabel('t value')
    #ax.set_title('Mean with min–max range')
    ax.legend(ncol=4, fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.axhline(4.5, color="black", linewidth=0.5) # Minimum Traces to Disclosure, significance threshold

    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/ntvla.png", dpi=150)

def plot_ntvla_composition(ntvla_list, metadata_filenames, ntvla_params, save_plots=False):
    savedplots_dir = None
    if save_plots:
        savedplots_dir = sharpwhisperer.get_new_plots_dir("comp_ntvla")
    
    metadata_text = ""
    metadata_text += f"filenames: {metadata_filenames}\n"
    metadata_text += f"ntvla_params: {ntvla_params}\n"
    metadata_text += "-" * 20
    metadata_text += "\n"
    for label, tc, res in ntvla_list:
        metadata_text += f"label {label}\n"
        #metadata_text += f"minnumtraces: {minnumtraces}\n"
        metadata_text += "\n"
    print("Plot metadata:")
    print("="*20)
    print(metadata_text)
    print()
    if savedplots_dir is not None:
        with open(f"{savedplots_dir}/plot_metadata.txt", "w") as f:
            f.write(metadata_text)

    # ====== plotting code
    fig, ax = plt.subplots(figsize=(8, 5))

    #colors = ['tab:blue','tab:orange','tab:green','tab:red','tab:purple']
    #assert len(ntvla_list) <= len(colors)

    for label, tc, res in ntvla_list:
        #assert 0 < len(colors)
        #color = colors.pop(0)
        assert res.shape == (tc.shape[0], 3)
        mean = res[:, 0]
        min_vals = res[:, 1]
        max_vals = res[:, 2]

        # Mean line
        line, = ax.plot(tc, mean, linewidth=2, label=label) #, color=color
        color = line.get_color()

        # Shaded band between min and max
        ax.fill_between(tc, min_vals, max_vals, color=color, alpha=0.2)
        #color = poly.get_facecolor()[0]

        # Optional: thin lines tracing the min and max edges
        ax.plot(tc, min_vals, color=color, alpha=0.4, linewidth=1)
        ax.plot(tc, max_vals, color=color, alpha=0.4, linewidth=1)


    ax.set_xlabel('Number of traces')
    ax.set_ylabel('t value')
    #ax.set_title('Mean with min–max range')
    ax.legend(ncol=4, fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.axhline(4.5, color="black", linewidth=0.5) # Minimum Traces to Disclosure, significance threshold

    plt.tight_layout()
    if savedplots_dir is None:
        plt.show()
    else:
        plt.savefig(f"{savedplots_dir}/ntvla.png", dpi=150)

