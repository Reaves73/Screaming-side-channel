import cwhardware
import sharpwhisperer
import sharptriggerer
from gnuradio_recorder import Recorder

import chipwhisperer as cw
import time
import datetime
from tqdm import tqdm
import numpy as np

def capture_init_dac(target, PLATFORM, do_sharppeak_init, run_dac_max):#, sharppeak_connected=True):
    sharpwhisperer.set_dac(target, 0)
    sharpwhisperer.set_gate(target, True)
    if do_sharppeak_init:
        sharpwhisperer.init_sharppeak(target, PLATFORM)
        #if sharppeak_connected:
        #    input("waiting. press enter when sharppeak_dac is plugged")
    if run_dac_max:
        sharpwhisperer.set_dac(target, 700)

def tracelist_to_nparray(traces_l):
    #print(trace_l[0].size)
    #print(trace_l[1].size)
    min_len = min(len(t) for t in traces_l)
    traces_l_trimmed = [t[:min_len] for t in traces_l]
    return np.stack(traces_l_trimmed)

def capture_core(config_dict):
    experiment_descr = {}
    experiment_name = config_dict["experiment_name"]
    experiment_dir = sharpwhisperer.get_new_experiment_dir(experiment_name)
    experiment_descr["experiment_dir"] = experiment_dir
    print(f"CAPTURING: experiment '{experiment_name}' in '{experiment_dir}'")
    #raise Exception()

    sharpwhisperer.save_capture_config(config_dict, f"{experiment_dir}/meta/capture_config.json")
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
        experiment_descr["cw_adc_rate_expected"] = cw_adc_rate_expected
        experiment_descr["cw_adc_rate_measured"] = cw_adc_rate_measured
        print("CW Sampling rate:", cw_adc_rate_measured)
        chipwhisperer_n_samples = round(duration_s * cw_adc_rate_measured)
        print("CW samples per trace:", chipwhisperer_n_samples)
        if chipwhisperer_n_samples > 24000: # it should be something like 24573, but I see errors with varying values, as low as 24431, so this seems safe enough
            raise Exception("maximum number of samples allowed is 24000")
        hw.scope.adc.samples = chipwhisperer_n_samples
    
    gr_force_dac = config_dict["force_dac"]
    rundacmax = sharpwhisperer.get_experiment_setup_rundacmax(cfg)
    assert (not gr_force_dac) or (rundacmax is None)
    rundacmax = gr_force_dac if rundacmax is None else rundacmax
    if include_trace_gnuradio:
        gr_samprate = config_dict["gnuradio_samplerate"]
        gr_centfreq = sharpwhisperer.get_experiment_setup_centfreq(cfg)
        gr_rxgain = sharpwhisperer.get_experiment_setup_rxgain(cfg)
        gr_sigpolarity = sharpwhisperer.get_experiment_setup_sigpolarity(cfg)

    #
    # INIT
    #

    sharpwhisperer.init_target(hw)

    #sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)

    # TODO: this is maybe not ideal, but it preserves the poor-man's error handling as endless loop in dacadc driver's dac_trigger function
    sharpwhisperer.set_gate(hw.target, False)
    sharpwhisperer.set_dac(hw.target, 350)

    if include_trace_gnuradio or gr_force_dac:
        if rundacmax:
            assert not sharpwhisperer.get_experiment_setup_config()["sharppeak_on_dac_directly"] #TODO: untested code, and this option doesn't look future-proof enough for what is needed here
        capture_init_dac(hw.target, PLATFORM, do_sharppeak_init=(not rundacmax), run_dac_max=rundacmax)

    #
    # CAPTURE
    #

    ktp = cw.ktp.Basic()

    if include_trace_chipwhisperer:
        traces_chipwhisperer = np.zeros([n_traces, chipwhisperer_n_samples], dtype=np.float32)
    if include_trace_gnuradio:
        #traces_gnuradio_l = []
        gnuradio_n_samples = round(duration_s * gr_samprate)
        traces_gnuradio = np.zeros([n_traces, gnuradio_n_samples], dtype=np.float32)
        q_gnuradio_trig = np.zeros([n_traces, 3], dtype=np.uint32)
        q_gnuradio_retries = np.zeros([n_traces, 3], dtype=np.uint32)

    plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
    ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
    keys = np.zeros([n_traces, 16], dtype=np.uint8)
    q_numcaptries = np.zeros([n_traces, 1], dtype=np.uint32)

    state = ktp.next()

    #target.set_key(key)

    last_complete_trace_idx = [None]
    def capture_fun(state, cap_handle=None, gr_fs=None):
        print("Capturing traces...")

        experiment_descr["capture_n_traces_complete"] = 0
        experiment_descr["capture_error_cw_no_trace"] = 0
        experiment_descr["capture_error_gr_trigger_missing"] = 0
        experiment_descr["capture_error_gr_trigger_invalid"] = 0
        experiment_descr["capture_error_gr_trace_incomplete"] = 0

        gr_trig_n_width = None
        if cap_handle is not None:
            assert gr_fs is not None
            gr_trig_n_width = round(5e-3 * gr_fs / 100)
            print("gr_trig_n_width:", gr_trig_n_width)
            gr_trig_n_permit_range = (4e-3 * gr_fs, 15e-3 * gr_fs)
            gr_trig_n_permit_diff = 4e-7 * gr_fs
            gr_trig_delay_samples = round(1e-4 * gr_fs)

        for i in tqdm(range(n_traces)): # NOTE: it is important for last_complete_trace_idx that this index i is starting from 0 and incrementing
            key, text = state

            capture_ok = False
            capture_retries_max = 10
            capture_tries = 0
            for _ in range(capture_retries_max):
                capture_tries += 1
                if cap_handle is not None:
                    cap_handle.record_start()
                ret = hw.capture(text, key)
                if cap_handle is not None:
                    time.sleep(0.02)
                    t_gnuradio = cap_handle.record_stop() * gr_sigpolarity

                    response = sharptriggerer.match_filter_convolution(t_gnuradio, gr_trig_n_width)
                    detected_trigger = sharptriggerer.match_filter_find_trigger(response, gr_trig_n_width)
                    if detected_trigger is None:
                        experiment_descr["capture_error_gr_trigger_missing"] += 1
                        print("gnuradio trace: trigger not found")
                        continue
                    _, _, (num_pos_peaks_diff, num_neg_peaks_diff) = detected_trigger
                    trig_end = sharptriggerer.get_trigger_end(detected_trigger, gr_trig_n_permit_range, gr_trig_n_permit_diff, gr_trig_delay_samples)
                    if trig_end is None:
                        # NOTE: e.g., not clean enough, overflow has happened so that at least one plateau is compressed
                        experiment_descr["capture_error_gr_trigger_invalid"] += 1
                        print("gnuradio trace: trigger signal not valid") 
                        continue
                    idx_left_cutoff, samples_left_right_diff = trig_end
                    idx_right_cutoff = idx_left_cutoff + gnuradio_n_samples#round(duration_s*gr_fs)
                    #print(t_gnuradio.size)
                    if t_gnuradio.size <= idx_right_cutoff:
                        experiment_descr["capture_error_gr_trace_incomplete"] += 1
                        print("gnuradio trace: trace not completely captured")
                        continue
                    t_gnuradio_cut = t_gnuradio[idx_left_cutoff:idx_right_cutoff]
                    #traces_gnuradio_l.append(t_gnuradio_cut)

                if ret is None:
                    experiment_descr["capture_error_cw_no_trace"] += 1
                    print("chipwhisperer: trace not captured")
                    continue

                capture_ok = True
                break
            if not capture_ok:
                raise Exception(f"after {capture_retries_max} capturing retries, no success")

            k = np.array(list(ret.key), dtype=np.uint8)
            c = np.array(list(ret.textout), dtype=np.uint8)
            p = np.array(list(ret.textin), dtype=np.uint8)

            t = np.array(list(ret.wave), dtype=np.float32)
            #t = np.array(ret.wave, dtype=np.float32)
            #tc = hw.scope.adc.trig_count
            #seg = t[int(tc/4): int(tc/4) + post_len]

            if include_trace_chipwhisperer:
                traces_chipwhisperer[i] = t
            if include_trace_gnuradio:
                traces_gnuradio[i] = t_gnuradio_cut
                q_gnuradio_trig[i] = np.array([
                    num_pos_peaks_diff,
                    num_neg_peaks_diff,
                    samples_left_right_diff])
                q_gnuradio_retries[i] = np.array([
                    experiment_descr["capture_error_gr_trigger_missing"],
                    experiment_descr["capture_error_gr_trigger_invalid"],
                    experiment_descr["capture_error_gr_trace_incomplete"]])
            #traces[i, :len(seg)] = seg
            plaintexts[i] = p
            ciphertexts[i] = c
            keys[i] = k
            q_numcaptries[i] = capture_tries
            
            state = ktp.next()
            last_complete_trace_idx[0] = i
            experiment_descr["capture_n_traces_complete"] += 1
        return state

    experiment_descr["capture_time_start"] = datetime.datetime.now().isoformat()
    try:
        if not include_trace_gnuradio:
            capture_fun(state)
        else:
            with Recorder(cent_freq=gr_centfreq, rx_gain=gr_rxgain) as r:
                r.set_samprate(gr_samprate)
                gr_fs = r.get_samprate()
                print(f"gnuradio_samplerate={gr_fs}")
                #NOTE: maybe this is not true later because not arbitrary values are settable and it is up to some signal synthesis like with CW?
                assert gr_samprate == gr_fs
                experiment_descr["gr_samplerate"] = gr_fs
                capture_fun(state, cap_handle=r, gr_fs=gr_fs)
    except KeyboardInterrupt:
        experiment_descr["capture_abort_reason"] = "KeyboardInterrupt"
        print("Capture abort requested by user.")
    except Exception as e:
        experiment_descr["capture_abort_reason"] = f"Exception [{e}]"
        raise
    finally:
        experiment_descr["capture_time_end"] = datetime.datetime.now().isoformat()
        sharpwhisperer.finalize_sharpwhisperer(hw)

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
                np.save(f"{experiment_dir}/traces_gnuradio.npy", traces_gnuradio[:n_tr,:]) #tracelist_to_nparray(traces_gnuradio_l)
                np.save(f"{experiment_dir}/quality/gnuradio_trig.npy", q_gnuradio_trig[:n_tr,:])
                np.save(f"{experiment_dir}/quality/gnuradio_retries.npy", q_gnuradio_retries[:n_tr,:])
            np.save(f"{experiment_dir}/keys.npy", keys[:n_tr,:])
            np.save(f"{experiment_dir}/plaintexts.npy", plaintexts[:n_tr,:])
            np.save(f"{experiment_dir}/ciphertexts.npy", ciphertexts[:n_tr,:])
            np.save(f"{experiment_dir}/quality/numcaptries.npy", q_numcaptries[:n_tr])

        sharpwhisperer.save_capture_config(experiment_descr, f"{experiment_dir}/meta/experiment_descr.json")

    return experiment_dir, experiment_descr

def capture_random_stuff_core(stuff_id, numtraces=None, fs=None):
    cfg = sharpwhisperer.get_experiment_setup_config()
    PLATFORM = sharpwhisperer.get_experiment_setup_config_PLATFORM(cfg)

    FIRMWARE = "simpleserial-aes"

    hw = cwhardware.CWHardware()
    hw.connect(PLATFORM)

    # Confiture scope
    hw.scope.default_setup();
    time.sleep(0.1)

    gr_sigpolarity = sharpwhisperer.get_experiment_setup_sigpolarity(cfg)
    rundacmax = sharpwhisperer.get_experiment_setup_rundacmax(cfg)
    assert rundacmax is not None

    sharpwhisperer.init_target(hw)
    traces_l = []
    try:
        capture_init_dac(hw.target, PLATFORM, do_sharppeak_init=(not rundacmax), run_dac_max=rundacmax)

        with Recorder(
            cent_freq=sharpwhisperer.get_experiment_setup_centfreq(cfg),
            rx_gain=sharpwhisperer.get_experiment_setup_rxgain(cfg)
        ) as r:
            r.set_samprate(fs)
            print(f"samprate={r.get_samprate()}")
            for _ in tqdm(range(1 if numtraces is None else numtraces)):
                r.record_start()
                time.sleep(0.01)
                sharpwhisperer.do_random_stuff(hw.target, stuff_id, debug=False)
                time.sleep(0.02)
                traces_l.append(r.record_stop() * gr_sigpolarity)
                time.sleep(0.2)
    finally:
        sharpwhisperer.finalize_sharpwhisperer(hw)
    if numtraces is None:
        assert len(traces_l) == 1
        return traces_l[0]
    return tracelist_to_nparray(traces_l)

capture = sharpwhisperer.sync_usage_wrapper(capture_core)
capture_random_stuff = sharpwhisperer.sync_usage_wrapper(capture_random_stuff_core)
