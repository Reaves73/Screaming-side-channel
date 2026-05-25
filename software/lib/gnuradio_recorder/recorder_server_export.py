import threading
import socket
import numpy as np
import struct
from io import BytesIO
import time

exportrunning = False
exportbuffers = [] # TODO: maybe better to send this in a queue?
exportfishedevent = threading.Event()

samprate = None

debug = False

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
#SAMPRATE_SET_CMD_PREFIX="SAMPRATE SET:"
#SAMPRATE_SET_CMD_SUFFIX=":"
def control_server(host="127.0.0.1", port=9999):
    global exportrunning, samprate

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
                    if debug:
                        print(f"start capturing")
                    conn.sendall(b"OK CAP START\n")

                elif data == CAPTURE_STOP_CMD:
                    if debug:
                        print(f"stop capturing")
                    #TODO: detect if overflow has happened during capture and send an error in this case
                    # signal stopping
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

                #TODO:
                #elif data.startswith(SAMPRATE_SET_CMD_PREFIX) and data.endswith(SAMPRATE_SET_CMD_SUFFIX):

                else:
                    conn.sendall(b"UNKNOWN CMD\n")
                    print(f"unknown command: {data}")
                    break
        except Exception as e:
            print("socket error:", e)
        finally:
            conn.close()
            print(f"disconnected: {addr}")

def init(samp_rate):
    global samprate
    samprate = samp_rate
    print(f"initing, samp_rate={samp_rate}")
    threading.Thread(target=control_server, daemon=True).start()

lastbuffer = None
exportrunning_onemore = False
def exportdata(d):
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
