import socket

CAPTURE_START_CMD_PREFIX="CAP START:"
CAPTURE_START_CMD_SUFFIX=":"
CAPTURE_STOP_CMD="CAP STOP"
class Recorder:
    def __init__(self, server=None):
        assert server != None # TODO: this is for trying to start the server in the background
        self._server = server
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        self._s.connect((self._server, 9999))
        return self

    def __exit__(self, type, value, traceback):
        self._s.close()

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

    with Recorder("127.0.0.1") as r:
        print("Capturing traces...")

        for i in range(n_traces):
            print("Trace", i)
            
            res = r.record_start(f"{traces_fname_prefix}{i}.bin")
            time.sleep(0.5)
            res = r.record_stop()
            #shutil.copy(sharppeak_trace_fname, trace_fname)
