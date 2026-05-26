import threading
import socket
import numpy as np
import struct
from io import BytesIO
import time
import sys

exportrunning = False
exportbuffers = [] # TODO: maybe better to send this in a queue?
exportrunning_onemore = False
exportfishedevent = threading.Event()

samprate = None

debug = False

send_async_msg_fn = None
def send_async_msg(msg):
    assert send_async_msg_fn is not None
    send_async_msg_fn(msg)

# NOTE: this works because the demodulation block doesn't rely on knowing the sampling rate
def set_samplingrate(samp_rate):
    global samprate
    if samprate == samp_rate:
        print(f"USRP: do nothing, samp_rate={samp_rate}")
        return
    msg = pmt.make_dict()
    msg = pmt.dict_add(msg, pmt.intern("rate"), pmt.from_float(samp_rate)) #pmt.from_float(45e6) # pmt.to_pmt(...)
    send_async_msg(msg)
    samprate = samp_rate
    print(f"USRP: updating, samp_rate={samp_rate}")
    # TODO: maybe better to synchronize via export_data. there might not data coming until that is done, or at least not after buffers are running empty
    time.sleep(1.0) # pause to let demodulation catch up to the change (hope this is enough and helps, 0.5 was too short, 0.8 seemed enough)

def send_array(sock, nparr):
    buf = BytesIO()
    np.save(buf, nparr, allow_pickle=False)

    data = buf.getvalue()

    # send length prefix first
    sock.sendall(struct.pack("!I", len(data)))
    sock.sendall(data)

CAPTURE_START_CMD="CAP START"
CAPTURE_STOP_CMD="CAP STOP"
SAMPRATE_GET_CMD="SAMPRATE GET"
SAMPRATE_SET_CMD_PREFIX="SAMPRATE SET:"
SAMPRATE_SET_CMD_SUFFIX=":"
def control_server(host="127.0.0.1", port=9999):
    global exportrunning, exportrunning_onemore, samprate

    while lastbuffer is None:
        time.sleep(0.1)

    #open a server to listen
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    print(f"listening on {host}:{port}")
    import os
    print(f"cwd: {os.getcwd()}")

    while True:
        conn, addr = s.accept()
        print(f"connected: {addr}")
        try:
            while True:
                data = conn.recv(1024).decode().strip()
                if len(data) == 0:
                    break
                #print(f"received: {data} from {addr}")

                if data == CAPTURE_START_CMD:
                    exportbuffers.clear()
                    exportrunning = True
                    # TODO: this while solution is not so great, should have a timeout, but prevents race condition at least
                    while not exportrunning_onemore:
                        time.sleep(0.001)
                    if debug:
                        print(f"start capturing")
                    conn.sendall(b"OK CAP START\n")

                elif data == CAPTURE_STOP_CMD:
                    if debug:
                        print(f"stop capturing")
                    # signal stopping
                    # TODO: don't need this race condition check actually, it is covered by the "while not exportrunning_onemore" in the start procedure
                    if not exportrunning_onemore:
                        print(f"race condition averted")
                        send_array(conn, np.array([]))
                        conn.sendall(b"FAIL CAP STOP\n")
                    exportrunning = False
                    # wait for ack, then clear it for next capture
                    exportfishedevent.wait()
                    exportfishedevent.clear()
                    # process buffers
                    if debug:
                        print(f"collected {len(exportbuffers)} buffers")
                    #print(type(exportbuffers[0]))
                    #print(exportbuffers[0].shape)
                    trace = np.concatenate(exportbuffers).astype(np.float32)
                    #print(trace.shape)
                    # send serialized through socket
                    if debug:
                        print(f"sending trace")
                    send_array(conn, trace)
                    conn.sendall(b"OK CAP STOP\n")

                elif data == SAMPRATE_GET_CMD:
                    if debug:
                        print(f"returning samp_rate")
                    conn.sendall(f"OK SAMPRATE GET:{samprate}\n".encode())

                elif data.startswith(SAMPRATE_SET_CMD_PREFIX) and data.endswith(SAMPRATE_SET_CMD_SUFFIX):
                    samp_rate = float(data[len(SAMPRATE_SET_CMD_PREFIX):-len(SAMPRATE_SET_CMD_SUFFIX)])
                    if debug:
                        print(f"received command to set new sample rate: {samp_rate}")
                    set_samplingrate(samp_rate)
                    conn.sendall(b"OK SAMPRATE SET\n")

                else:
                    conn.sendall(b"UNKNOWN CMD\n")
                    print(f"unknown command: {data}")
                    break
        except Exception as e:
            print("RECORDER_SERVER error: during socket handling:", e, file=sys.stderr)
        finally:
            conn.close()
            exportrunning = False
            try:
                print(f"disconnected: {addr}")
            except BrokenPipeError:
                print("RECORDER_SERVER error: cannot print to stdout, pipe broken (other process died?)", file=sys.stderr)

def init(samp_rate):
    global samprate
    samprate = samp_rate
    print(f"USRP: initing, samp_rate={samp_rate}")
    threading.Thread(target=control_server, daemon=True).start()

lastbuffer = None
def export_data(d):
    global lastbuffer, exportrunning_onemore

    if not exportrunning:
        # collect one more buffer at the end and signal completion
        if exportrunning_onemore:
            exportbuffers.append(d.copy())
            exportrunning_onemore = False
            # send signal to be done
            exportfishedevent.set()
            return
        lastbuffer = d.copy()
        return

    # collect one more buffer in the beginning (the last one)
    if len(exportbuffers) == 0:
        assert not (lastbuffer is None)
        exportbuffers.append(lastbuffer)
        lastbuffer = None
        exportrunning_onemore = True
    exportbuffers.append(d.copy())
    if debug:
        print(".", end="", flush="True")

# NOTE: cannot detect whether overflow has happened during capture, as these messages are asynchronous and in case of many overflows are
# NOTE: could only tear down the whole server to radically mark data reliability issue in case of many overflows happening at the same time at some point
# NOTE: but then, what value would be good to also avoid unnecessary false alarms?
import pmt
def handle_async_msg(msg):
    print("!! USRP: ", type(msg), msg)
    return None
    #<class 'pmt.pmt_python.pmt_base'> (uhd_async_msg (overflows . 2))
    msg_p = pmt.to_python(msg)
    print(msg_p)
    if msg_p[0] == "uhd_async_msg":
        uhd_am_d = msg_p[1]
        try:
            n_overflows = uhd_am_d["overflows"]
            print("Overflows detected:", n_overflows)
        except:
            pass
    #if pmt.is_pair(msg):
    #    v_l = pmt.car(msg)
    #    v_r = pmt.cdr(msg)
    #    if pmt.symbol_to_string(v_l) == "uhd_async_msg":
    #        #print(v_r)
    #        #print(pmt.is_pair(v_r))
    #        #print(pmt.is_dict(v_r))
    #        if pmt.is_dict(v_r):
    #            k_uhdam_overflows = pmt.intern("overflows")
    #            if pmt.dict_has_key(v_r, k_uhdam_overflows):
    #                n_overflows_pmt = pmt.dict_ref(v_r, k_uhdam_overflows, pmt.PMT_NIL)
    #                if pmt.is_number(n_overflows_pmt):
    #                    n_overflows = pmt.to_python(n_overflows_pmt)
    #                    print("Overflows detected:", n_overflows, type(n_overflows))
    return None
