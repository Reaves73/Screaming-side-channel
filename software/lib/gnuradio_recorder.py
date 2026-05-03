import socket
import subprocess
import threading
import os

def print_recorder_server(p):
    for line in p.stdout:
        print(f"------ {line}", end="", flush=True)

def start_recorder_server():
    cmd_script = f"{os.path.dirname(os.path.realpath(__file__))}/gnuradio_recorder/recorder_server.py"
    cmd = ["/usr/bin/python3", "-u", cmd_script]

    p = None
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in p.stdout:
            print(f"------ {line}", end="", flush=True)
            if "listening on " in line:
                break
    except:
        if not (p is None):
            p.kill()
        raise
    # create thread that collects lines from p.stdout and prints to own stdout
    threading.Thread(target=print_recorder_server, args=(p,), daemon=True).start()
    return p

def stop_recorder_server(p):
    p.kill()

CAPTURE_START_CMD_PREFIX="CAP START:"
CAPTURE_START_CMD_SUFFIX=":"
CAPTURE_STOP_CMD="CAP STOP"
class Recorder:
    def __init__(self, server=None):
        if server is None:
            print("running recorder_server in background")
        self._server = server
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._p = None

    def __enter__(self):
        server_address = self._server
        if server_address is None:
            # start the server in the background
            server_address = "127.0.0.1"
            self._p = start_recorder_server()
        self._s.connect((server_address, 9999))
        return self

    def __exit__(self, type, value, traceback):
        self._s.close()
        p = self._p
        if not(p is None):
            stop_recorder_server(p)

    def _send_cmd(self, cmd):
        #print(f"- sending '{cmd}'")
        self._s.sendall(cmd.encode())
        res = self._s.recv(1024).decode().strip()
        #print(res)
        if res.split(":")[0] == "OK " + cmd.split(":")[0]:
            return res
        raise Exception(res)

    def record_start(self, filename):
        self._send_cmd(CAPTURE_START_CMD_PREFIX + filename + CAPTURE_START_CMD_SUFFIX)

    def record_stop(self):
        self._send_cmd(CAPTURE_STOP_CMD)


if __name__ == '__main__':
    import os
    import time
    n_traces = 5
    tracesdir = (os.getcwd()) + "/traces"
    os.makedirs(tracesdir, exist_ok=True)
    traces_fname_prefix = f"{tracesdir}/tr_"

    server_address = None
    #server_address = "127.0.0.1"
    with Recorder(server_address) as r:
        print("Capturing traces...")

        for i in range(n_traces):
            print("Trace", i)
            
            r.record_start(f"{traces_fname_prefix}{i}.bin")
            time.sleep(0.5)
            r.record_stop()
            #shutil.copy(sharppeak_trace_fname, trace_fname)
