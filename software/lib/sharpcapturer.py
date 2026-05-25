import cwhardware
import sharpwhisperer
import sharptriggerer
from gnuradio_recorder import Recorder

import chipwhisperer as cw
import time
import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import json
import os
from pwd import getpwuid

def save_capture_config(config_dict, path):
    with open(path, 'w') as config_file:
        json.dump(config_dict, config_file, indent=2)

def tracelist_to_nparray(traces_l):
    #print(trace_l[0].size)
    #print(trace_l[1].size)
    min_len = min(len(t) for t in traces_l)
    traces_l_trimmed = [t[:min_len] for t in traces_l]
    return np.stack(traces_l_trimmed)

def capture(config_dict):
    experiment_descr = {}
    experiment_name = config_dict["experiment_name"]
    experiment_dir = sharpwhisperer.get_new_experiment_dir(experiment_name)
    experiment_descr["experiment_dir"] = experiment_dir
    print(f"CAPTURING: experiment '{experiment_name}' in '{experiment_dir}'")
    #raise Exception()

    save_capture_config(config_dict, f"{experiment_dir}/meta/capture_config.json")
    # save repository commit and diff
    sharpwhisperer.write_git_diff_files(f"{experiment_dir}/meta")

    cfg = sharpwhisperer.get_experiment_setup_config(f"{experiment_dir}/meta")
    PLATFORM = sharpwhisperer.get_experiment_setup_config_PLATFORM(cfg)
    # firmware is fixed right now in this function
    FIRMWARE = "simpleserial-aes" #config_dict["FIRMWARE"]
    print("PLATFORM: ", PLATFORM)
    print("FIRMWARE: ", FIRMWARE)

    duration_s = config_dict["duration_s"]
    n_traces = config_dict["n_traces"]

    include_trace_chipwhisperer = config_dict["include_trace_chipwhisperer"]
    include_trace_gnuradio = config_dict["include_trace_gnuradio"]

    #
    # SETUP
    #

    hw = cwhardware.CWHardware()
    hw.connect(PLATFORM)

    # Confiture scope
    hw.scope.default_setup();
    hw.scope.adc.decimate = config_dict["chipwhisperer_n_decimate"]
    print("CW Sys Clock:", hw.scope.clock._hwinfo.sysFrequency())
    cw_clkgen_freq_set = hw.scope.clock.clkgen_freq
    print("CW Target clock freq setting:", cw_clkgen_freq_set)
    # CW clock settings
    if config_dict["chipwhisperer_adc_clkgen_x4"]:
        hw.scope.clock.adc_src = "clkgen_x4"
    else:
        hw.scope.clock.adc_src = "clkgen_x1"
    if not hw.scope.try_wait_clkgen_locked(5, 0.05):
        raise Exception("Could not lock clock for scope. You have to run the script again.")
    # need a good delay to get a proper adc_rate reading from CW (otherwise it is weirdly and randomly off)
    time.sleep(0.5)

    # determine CW clocks
    cw_adc_rate_expected = hw.scope.clock.adc_mul * cw_clkgen_freq_set / hw.scope.adc.decimate
    cw_adc_rate_measured = hw.scope.clock.adc_rate
    cw_clkgen_freq_inferred = cw_adc_rate_measured / hw.scope.clock.adc_mul * hw.scope.adc.decimate

    # validate measured with expected, and set with inferred
    if not(abs(cw_adc_rate_expected-cw_adc_rate_measured) < cw_adc_rate_expected*1e-6 and
           abs(cw_clkgen_freq_set-cw_clkgen_freq_inferred) < cw_clkgen_freq_set*1e-6):
        print("cw_adc_rate_expected:   ", cw_adc_rate_expected)
        print("cw_adc_rate_measured:   ", cw_adc_rate_measured)
        print("cw_clkgen_freq_set:     ", cw_clkgen_freq_set)
        print("cw_clkgen_freq_inferred:", cw_clkgen_freq_inferred)
        raise Exception("measured adc and inferred clkgen frequencies not validated.")

    # NOTE: could reset cached adc_rate value in CW library, measure again and validate, if we would be interested in that

    if include_trace_chipwhisperer:
        experiment_descr["cw_adc_rate_measured"] = cw_adc_rate_measured
        print("CW Sampling rate:", cw_adc_rate_measured)
        chipwhisperer_n_samples = round(duration_s * cw_adc_rate_measured)
        print("CW samples per trace:", chipwhisperer_n_samples)
        if chipwhisperer_n_samples > 24000: # it should be something like 24573, but I see errors with varying values, as low as 24431, so this seems safe enough
            raise Exception("maximum number of samples allowed is 24000")
        hw.scope.adc.samples = chipwhisperer_n_samples

    #
    # INIT
    #

    sharpwhisperer.init_target(hw)
    #sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)
    if include_trace_gnuradio:
        sharpwhisperer.set_dac(hw.target, 0)
        sharpwhisperer.set_gate(hw.target, True)
        sharpwhisperer.init_sharppeak(hw.target, PLATFORM)
    else:
        # TODO: this is maybe not ideal, but it preserves the poor-man's error handling as endless loop in dacadc driver's dac_trigger function
        sharpwhisperer.set_gate(hw.target, False)
        sharpwhisperer.set_dac(hw.target, 350)

    #
    # CAPTURE
    #

    ktp = cw.ktp.Basic()

    if include_trace_chipwhisperer:
        traces_chipwhisperer = np.zeros([n_traces, chipwhisperer_n_samples], dtype=np.float32)
    traces_gnuradio_l = []

    plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
    ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
    keys = np.zeros([n_traces, 16], dtype=np.uint8)

    state = ktp.next()

    #target.set_key(key)

    last_complete_trace_idx = [None]
    def capture_fun(state, cap_handle=None, gr_fs=None):
        print("Capturing traces...")

        gr_trig_n_width = None
        if cap_handle is not None:
            assert gr_fs is not None
            gr_trig_n_width = round(5e-3 * gr_fs / 100)
            print("gr_trig_n_width:", gr_trig_n_width)
            gr_trig_n_permit_range = (4e-3 * gr_fs, 15e-3 * gr_fs)
            gr_trig_n_permit_diff = 4e-7 * gr_fs

        dstr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tracefile = f"{tempfile.gettempdir()}/traces_gnuradio_{dstr}.npy"
        for i in tqdm(range(n_traces)): # NOTE: it is important for last_complete_trace_idx that this index i is starting from 0 and incrementing
            key, text = state
            while True:
                if cap_handle is not None:
                    cap_handle.record_start(tracefile)
                ret = hw.capture(text, key)
                if cap_handle is not None:
                    time.sleep(0.02)
                    try:
                        cap_handle.record_stop()
                        t_gnuradio = np.load(tracefile)

                        response = sharptriggerer.match_filter_convolution(t_gnuradio, gr_trig_n_width)
                        detected_trigger = sharptriggerer.match_filter_find_trigger(response)
                        if detected_trigger is None:
                            print("gnuradio trace: trigger not found")
                            continue
                        idx_left_cutoff = sharptriggerer.get_trigger_end(detected_trigger, gr_trig_n_permit_range, gr_trig_n_permit_diff)
                        if idx_left_cutoff is None:
                            print("gnuradio trace: trigger signal not valid")
                            continue
                        idx_right_cutoff = idx_left_cutoff + round(duration_s*gr_fs)
                        #print(t_gnuradio.size)
                        if t_gnuradio.size <= idx_right_cutoff:
                            print("gnuradio trace: trace not completely captured")
                            continue
                        t_gnuradio_cut = t_gnuradio[idx_left_cutoff:idx_right_cutoff]
                        traces_gnuradio_l.append(t_gnuradio_cut)
                    finally:
                        if os.path.exists(tracefile):
                            os.remove(tracefile)

                if ret is None:
                    print("chipwhisperer: trace not captured")
                    continue

                break
            k = np.array(list(ret.key), dtype=np.uint8)
            c = np.array(list(ret.textout), dtype=np.uint8)
            p = np.array(list(ret.textin), dtype=np.uint8)

            t = np.array(list(ret.wave), dtype=np.float32)
            #t = np.array(ret.wave, dtype=np.float32)
            #tc = hw.scope.adc.trig_count
            #seg = t[int(tc/4): int(tc/4) + post_len]

            if include_trace_chipwhisperer:
                traces_chipwhisperer[i] = t
            #traces[i, :len(seg)] = seg
            plaintexts[i] = p
            ciphertexts[i] = c
            keys[i] = k
            
            state = ktp.next()
            last_complete_trace_idx[0] = i
        return state

    try:
        if not include_trace_gnuradio:
            capture_fun(state)
        else:
            with Recorder() as r:
                gr_fs = r.get_samprate()
                print(f"gnuradio_samplerate={gr_fs}")
                assert config_dict["gnuradio_samplerate"] == gr_fs #maybe this is not true later because not arbitrary values are settable and it is up to some signal synthesis like with CW?
                experiment_descr["gr_samplerate"] = gr_fs
                capture_fun(state, cap_handle=r, gr_fs=gr_fs)
    except KeyboardInterrupt:
        experiment_descr["capture_abort_reason"] = "KeyboardInterrupt"
        print("Aborting capture.")
        # reset CW target because we might have disturbed simpleserial
        sharpwhisperer.init_target(hw)
    except:
        experiment_descr["capture_abort_reason"] = "Exception"
        # reset CW target because the exception might have disturbed simpleserial
        sharpwhisperer.init_target(hw)
    finally:
        try:
            sharpwhisperer.set_dac(hw.target, 0)
            sharpwhisperer.set_gate(hw.target, False)
            # DISCONNECT
            hw.disconnect()
        except:
            print("ERROR: failed to set DAC, gate and disconnect from target")

        if last_complete_trace_idx[0] == n_traces - 1:
            experiment_descr["capture_complete"] = True
        else:
            experiment_descr["capture_complete"] = False
            print("WARNING: not all traces have been captured")
            print(f"Complete traces: {last_complete_trace_idx[0]+1 if last_complete_trace_idx[0] is not None else None}")

        if last_complete_trace_idx[0] is not None:
            n_tr = last_complete_trace_idx[0]+1
            if include_trace_chipwhisperer:
                np.save(f"{experiment_dir}/traces_chipwhisperer.npy", traces_chipwhisperer[:n_tr,:])
            if include_trace_gnuradio:
                np.save(f"{experiment_dir}/traces_gnuradio.npy", tracelist_to_nparray(traces_gnuradio_l)[:n_tr,:])
            np.save(f"{experiment_dir}/keys.npy", keys[:n_tr,:])
            np.save(f"{experiment_dir}/plaintexts.npy", plaintexts[:n_tr,:])
            np.save(f"{experiment_dir}/ciphertexts.npy", ciphertexts[:n_tr,:])

        save_capture_config(experiment_descr, f"{experiment_dir}/meta/experiment_descr.json")

    return experiment_dir, experiment_descr

# wrapper for capture function that synchronizes the users
import fcntl
def sync_capture(config_dict):
    LOCKFILE = f"{sharpwhisperer.get_experiments_dir()}/SHARPPEAK_LOCK"
    lock_fd = os.open(LOCKFILE, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    locked = False
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        # here we have the actual call to capture
        return capture(config_dict)
    except BlockingIOError:
        print("Another process is already capturing")
        
        # show owner of LOCKFILE
        print("LOCKFILE OWNER:", getpwuid(os.stat(LOCKFILE).st_uid).pw_name)
        #for (root, dirs, file) in os.walk(os.path.basename(LOCKFILE)):
        #    for f in file:
        #        if f.startswith(LOCKFILE):
        #            print(f)
        
        return None
    finally:
        if locked:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            finally:
                if os.path.exists(LOCKFILE):
                    os.remove(LOCKFILE)
