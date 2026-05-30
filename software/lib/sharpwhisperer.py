import os
REPOPATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")

import time
import datetime
import shutil
import json
import subprocess

# ---------------------------

def get_experiments_dir():
    experiments_dir_var = "SHARPWHISPERER_EXPERIMENTS"
    if experiments_dir_var not in os.environ:
        raise Exception(f"environment variable '{experiments_dir_var}' not defined")
    v = os.environ[experiments_dir_var]
    if not os.path.isdir(v):
        raise Exception(f"environment variable '{experiments_dir_var}' does not refer to existing directory '{v}'")
    return v

def get_experiment_setup_config_path(config_dir=None):
    if config_dir is None:
        config_dir = get_experiments_dir()
    return f"{config_dir}/setup_config.json"

def validate_experiment_setup_config(cfg):
    platforms = cfg["PLATFORMS"]
    assert all(map(lambda p: "ID" in p, platforms))
    assert all(map(lambda p: type(p["selected"]) == bool, platforms))
    assert len(list(filter(lambda p: p["selected"] == True, platforms))) == 1

    assert type(cfg["vdda_via_shunt"]) == bool
    assert type(cfg["shunt_shorted"]) == bool

    assert type(cfg["chipwhisperer_adc_to_target_power"]) == bool
    assert type(cfg["chipwhisperer_adc_to_dac"]) == bool
    assert type(cfg["sharppeak_on_dac_directly"]) == bool

    assert cfg["chipwhisperer_adc_to_target_power"] ^ cfg["chipwhisperer_adc_to_dac"]
    assert not(cfg["chipwhisperer_adc_to_dac"] and cfg["sharppeak_on_dac_directly"])

    assert type(cfg["notes"]) == str

def get_experiment_setup_config_PLATFORM(cfg):
    platforms = cfg["PLATFORMS"]
    return ((list(filter(lambda p: p["selected"] == True, platforms)))[0])["ID"]

def get_experiment_setup_config(experiment_dir=None):
    configpath = get_experiment_setup_config_path(experiment_dir)
    with open(configpath, 'r') as f:
        cfg = json.load(f)
    validate_experiment_setup_config(cfg)
    return cfg

def get_new_experiment_dir(experiment_name):
    experiments_dir = get_experiments_dir()
    dstr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    username = os.environ.get("USER")
    assert username is not None
    assert username != ""
    userpath = f"{experiments_dir}/{username}"
    if (not os.path.isdir(userpath)):
        os.mkdir(userpath)
    path = f"{userpath}/{dstr}_{experiment_name}"
    get_experiment_setup_config() # to validate the setup config
    os.mkdir(path)
    os.mkdir(f"{path}/meta")
    os.mkdir(f"{path}/quality")
    shutil.copyfile(get_experiment_setup_config_path(), get_experiment_setup_config_path(f"{path}/meta"))
    return path

def save_capture_config(config_dict, path):
    with open(path, 'w') as config_file:
        json.dump(config_dict, config_file, indent=2, sort_keys=True)

# ---------------------------

def write_file(filename, d, binary=False):
    import os
    if os.path.exists(filename):
        raise Exception(f"file already exists: {filename}")
    with open(filename, "wb" if binary else "w", encoding=None if binary else "utf-8") as file:
        file.write(d)

def write_git_diff_files(dirpath):
    prev_cwd = os.getcwd()
    os.chdir(REPOPATH)
    #print(os.getcwd())
    hash = subprocess.check_output(["git", "rev-parse", "HEAD"])
    commit = subprocess.check_output(["git", "log", "-1"])
    diff = subprocess.check_output(["git", "diff"])
    diff_staged = subprocess.check_output(["git", "diff", "--staged"])
    os.chdir(prev_cwd)
    #print(os.getcwd())
    write_file(f"{dirpath}/githash.txt", hash, binary=True)
    write_file(f"{dirpath}/gitcommit.txt", commit, binary=True)
    write_file(f"{dirpath}/gitdiff.txt", diff, binary=True)
    write_file(f"{dirpath}/gitdiff_staged.txt", diff_staged, binary=True)

# ---------------------------

# wrapper for procedures that use chipwhisperer HW, or other shared resources; this is to synchronize the users
import fcntl
from pwd import getpwuid
def sync_usage_wrapper(fn):
    def wrapped(*args, **kwargs):
        LOCKFILE = f"{get_experiments_dir()}/SHARPPEAK_LOCK"
        lock_fd = os.open(LOCKFILE, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        locked = False
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            # here we have the actual call to capture
            return fn(*args, **kwargs)
        except BlockingIOError:
            print("Another process is already occupying the shared sharpwhisperer resource.")
            
            # show owner of LOCKFILE
            print("LOCKFILE OWNER:", getpwuid(os.stat(LOCKFILE).st_uid).pw_name)
            
            return None
        finally:
            if locked:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                finally:
                    if os.path.exists(LOCKFILE):
                        os.remove(LOCKFILE)
    return wrapped

# ---------------------------

# enabled or disables DAC output
def set_gate(target, enabled):
    if enabled:
        target.simpleserial_write('u', bytearray([0, 1, 0]))
        #print(f"gate set to 1.")
    else:
        target.simpleserial_write('u', bytearray([0, 0, 0]))
        #print(f"gate set to 0.")
    print(f"Gate set to {'ENABLED' if enabled else 'DISABLED'}.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def set_dac(target, value):
    assert 0 <= value <= 700
    payload = bytearray([1, (value >> 8) & 0xFF, value & 0xFF])
    target.simpleserial_write('u', payload)
    print(f"DAC set to {value}.")
    resp = target.simpleserial_read('g', 1)
    assert resp[0] == 1
    #return resp

def get_adc(target):
    payload = bytearray([2, 0, 0])
    target.simpleserial_write('u', payload)
    print(f"ADC value requested.")
    resp = target.simpleserial_read('g', 2)
    #print(resp)
    
    return int.from_bytes(resp, byteorder='big')

def do_random_stuff(target, stuff_id, debug=True):
    payload = bytearray([3, stuff_id & 0xFF, 0])
    target.simpleserial_write('u', payload)
    if debug:
        print(f"doing random stuff {stuff_id} requested.")
    resp = target.simpleserial_read('g', 1, timeout=10000) # timeout is in ms
    if resp[0] != 1:
        print("random stuff failed")

def get_platform_id(target):
    target.simpleserial_write('u', bytearray([4, 0, 0]))
    resp = target.simpleserial_read('g', 1)
    assert resp[0] != 0
    if resp[0] == 1:
        return "CW308_STM32F0"
    elif resp[0] == 2:
        return "CW308_STM32F3"
    elif resp[0] == 3:
        return "CW308_STM32L4"
    else:
        return "UNKNOWN"

# ---------------------------

def get_firmware(PLATFORM, FIRMWARE):
    return f'{REPOPATH}/firmware/{FIRMWARE}/{FIRMWARE}-{PLATFORM}.hex'

def set_target_power(scope, on, do_print=False):
    scope.io.target_pwr = on
    if do_print:
        print(f"Target turned {'on' if on else 'off'}")

def reset_target(scope):
    set_target_power(scope, False)
    time.sleep(0.5)
    set_target_power(scope, True)
    time.sleep(0.5)

def init_target(hw):
    reset_target(hw.scope)
    hw.target.flush()
    hw.reset_target()
    time.sleep(0.1)

    # test at the end
    target_platform = get_platform_id(hw.target)
    print(f"target replies as {target_platform}")
    return target_platform
    #resp = get_adc(hw.target)
    #print("- ADC reply:", resp)

def compile_firmware(PLATFORM, FIRMWARE):
    # run compilation
    res = os.system(f"{REPOPATH}/firmware/compile.sh {PLATFORM}")
    print(f"compilation result: {res}")
    return res

def program_target(PLATFORM, FIRMWARE, hw, compile=True):
    fw_path = get_firmware(PLATFORM, FIRMWARE)
    if compile:
        res = compile_firmware(PLATFORM, FIRMWARE)
        assert res == 0
    reset_target(hw.scope)
    print("- progromming hex to target chip")
    print(f"- firmware: {fw_path}")
    hw.program_target(fw_path)

    # run an init at the end
    target_platform = init_target(hw)
    if target_platform != PLATFORM:
        print(f"target reports unexpected id directly after programming: {target_platform}")
        assert False

# TODO: should probably implement this and the locking as a context manager
def finalize_sharpwhisperer(hw):
    # TODO: there might be a better way to just resynchronize simpserial communication
    # first determine if simpserial is still functional, if not init the target again to bring it into a defined state
    try:
        # probe if simpserial communication is usable, this call should always succeed in this case
        assert get_platform_id(hw.target) == hw.platform
    except:
        # reset CW target because the exception might have disturbed simpleserial
        print("INFO: resetting target to reenable simpserial")
        init_target(hw)
    # make sure to not raise Exceptions so that this can be the "finally" cleanup code everywhere
    try:
        # set DAC to 0, turn off gate, power off the MCU
        set_dac(hw.target, 0)
        set_gate(hw.target, False)
        #set_target_power(hw.scope, False, do_print=True)
        # DISCONNECT
        hw.disconnect()
    except Exception as e:
        print("ERROR: failed to zero DAC, disable gate, turn off MCU power, and disconnect from target")
        print(f"ERROR: uncaught exception when finalizing!!! {e}")

# ---------------------------

def init_sharppeak(target, PLATFORM, i = 0):
    if i == 0:
        set_dac(target, 0)
        time.sleep(0.1)
        v = 700
        while v >= 350:
            set_dac(target, v)
            time.sleep(0.1)
            v -= 50
        if PLATFORM == "CW308_STM32F3":
            #set_dac(target, 357)
            #time.sleep(0.1)
            pass
        elif PLATFORM == "CW308_STM32F0":
            # 305 works with VDDA before shunt resistor
            set_dac(target, 324) # 324 works with VDDA and VDDA behind shunt resistor
            time.sleep(0.1)
        elif PLATFORM == "CW308_STM32L4":
            set_dac(target, 320)
            time.sleep(0.1)
            set_dac(target, 290)
            time.sleep(0.1)
            set_dac(target, 271) # works with VDDA and VDDA behind shunt resistor
            time.sleep(0.1)
        resp = get_adc(target)
        print("- ADC value:", resp)
        return True

    elif i == 1:
        set_dac(target, 0)
        time.sleep(2)
        v = 700
        while v >= 400:
            set_dac(target, v)
            time.sleep(0.5)
            v -= 50

        resp = get_adc(target)
        print("- ADC value:", resp)
        return True

    raise Exception()
