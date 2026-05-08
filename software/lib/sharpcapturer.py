import cwhardware
import sharpwhisperer
from gnuradio_recorder import Recorder

import chipwhisperer as cw
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import tempfile

def capture(config_dict):
    experiment_name = config_dict["experiment_name"]
    experiment_dir = sharpwhisperer.get_new_experiment_dir(experiment_name)
    print(f"CAPTURING: experiment '{experiment_name}' in '{experiment_dir}'")
    #raise Exception()

    PLATFORM = config_dict["PLATFORM"]
    # firmware is fixed right now in this function
    FIRMWARE = "simpleserial-aes" #config_dict["FIRMWARE"]
    print("PLATFORM: ", PLATFORM)
    print("FIRMWARE: ", FIRMWARE)

    n_traces = config_dict["n_traces"]

    include_trace_chipwhisperer = config_dict["include_trace_chipwhisperer"]
    include_trace_gnuradio = config_dict["include_trace_gnuradio"]
    
    if include_trace_chipwhisperer:
        chipwhisperer_n_samples = config_dict["chipwhisperer_n_samples"]
        chipwhisperer_n_decimate = config_dict["chipwhisperer_n_decimate"]

    #
    # SETUP
    #

    hw = cwhardware.CWHardware()
    hw.connect(PLATFORM)

    # Confiture scope
    hw.scope.default_setup();
    if include_trace_chipwhisperer:
        hw.scope.adc.samples = chipwhisperer_n_samples
        hw.scope.adc.decimate = chipwhisperer_n_decimate
        hw.scope.clock.adc_src = "clkgen_x1"
    time.sleep(0.1)

    if include_trace_chipwhisperer:
        print("Target clock freq:", hw.scope.clock.clkgen_freq)
        print("Sampling rate:", hw.scope.clock.adc_rate)

    #
    # INIT
    #

    sharpwhisperer.init_target(hw)
    #sharpwhisperer.program_target(PLATFORM, FIRMWARE, hw)
    sharpwhisperer.set_dac(hw.target, 0)
    #sharpwhisperer.set_gate(hw.target, True)
    sharpwhisperer.init_sharppeak(hw.target)


    #
    # CAPTURE
    #

    ktp = cw.ktp.Basic()

    traces = None
    if include_trace_chipwhisperer:
        traces_chipwhisperer = np.zeros([n_traces, chipwhisperer_n_samples], dtype=np.float32)

    plaintexts = np.zeros([n_traces, 16], dtype=np.uint8)
    ciphertexts = np.zeros([n_traces, 16], dtype=np.uint8)
    keys = np.zeros([n_traces, 16], dtype=np.uint8)

    state = ktp.next()

    #target.set_key(key)

    def capture_fun(state, cap_handle=None):
        key, text = state
        print("Capturing traces...")

        for i in tqdm(range(n_traces)):
            while True:
                if cap_handle is not None:
                    tracefile = f"{tempfile.gettempdir()}/traces_gnuradio.npy"
                    cap_handle.record_start(tracefile)
                ret = hw.capture(text, key)
                if cap_handle is not None:
                    time.sleep(0.02)
                    cap_handle.record_stop()

                if ret is not None:
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
        return state

    try:
        if not include_trace_gnuradio:
            capture_fun(state)
        else:
            with Recorder() as r:
                print(f"samprate={r.get_samprate()}")
                capture_fun(state, r)
    finally:
        sharpwhisperer.set_dac(hw.target, 0)
        sharpwhisperer.set_gate(hw.target, False)
        # DISCONNECT
        hw.disconnect()

    if include_trace_chipwhisperer:
        np.save(f"{experiment_dir}/traces_chipwhisperer.npy", traces)
    if include_trace_gnuradio:
        #TODO
        pass
    np.save(f"{experiment_dir}/keys.npy", keys)
    np.save(f"{experiment_dir}/plaintexts.npy", plaintexts)
    np.save(f"{experiment_dir}/ciphertexts.npy", ciphertexts)
