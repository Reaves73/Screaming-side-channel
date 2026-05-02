import threading
import socket
import numpy as np

exportrunning = False
exportbuffers = [] # TODO: maybe better to send this in a queue?
exportfishedevent = threading.Event()

CAPTURE_START_CMD_PREFIX="CAP START:"
CAPTURE_START_CMD_SUFFIX=":"
CAPTURE_STOP_CMD="CAP STOP"
def control_server(host="127.0.0.1", port=9999):
    global exportrunning

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
            export_filename = None
            while True:
                data = conn.recv(1024).decode().strip()
                if len(data) == 0:
                    break
                #print(f"received: {data} from {addr}")

                if data.startswith(CAPTURE_START_CMD_PREFIX) and data.endswith(CAPTURE_START_CMD_SUFFIX):
                    exportbuffers.clear()
                    exportrunning = True
                    print(f"start capturing")
                    export_filename = data[len(CAPTURE_START_CMD_PREFIX):-len(CAPTURE_START_CMD_SUFFIX)]
                    print(f"registered filename: {export_filename}")
                    conn.sendall(b"OK CAP START\n")

                elif data == CAPTURE_STOP_CMD:
                    print(f"stop capturing")
                    # signal stopping
                    exportrunning = False
                    # wait for ack, then clear it for next capture
                    exportfishedevent.wait()
                    exportfishedevent.clear()
                    # process buffers
                    print(f"collected {len(exportbuffers)} buffers")
                    #print(type(exportbuffers[0]))
                    #print(exportbuffers[0].shape)
                    trace = np.concatenate(exportbuffers).astype(np.float32)
                    #print(trace.shape)
                    # save to file
                    try:
                        np.save(export_filename, trace)
                        print(f"saved to: {export_filename}")
                        conn.sendall(b"OK CAP STOP\n")
                    except:
                        print(f"saving failed: {export_filename}")
                        conn.sendall(b"FAIL CAP STOP: saving\n")

                else:
                    conn.sendall(b"UNKNOWN CMD\n")
                    print(f"unknown command: {data}")
                    break
        except Exception as e:
            print("socket error:", e)
        finally:
            conn.close()
            print(f"disconnected: {addr}")

def init():
    print("initing")
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
        exportbuffers.append(lastbuffer)
        lastbuffer = None
        exportrunning_onemore = True
    exportbuffers.append(d.copy())
