import sys
import time
import signal
import socket
import threading
import shutil


n_traces = 5
traces_fname_prefix = "traces/tr_"
sharppeak_trace_fname = "/home/parallels/Desktop/cw-code/data_sharppeak/sharppeak"


def send_trigger(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9999))
    s.sendall(cmd.encode())
    res = s.recv(1024).decode().strip()
    s.close()
    return res


#
# CAPTURE
#

print("Capturing traces...")

for i in range(n_traces):
    print("Trace", i)
    
    trace_fname = f"{traces_fname_prefix}{i}.bin"
    res = send_trigger("capture_start")
    print(res)
    time.sleep(0.5)
    res = send_trigger("capture_stop:"+trace_fname)
    print(res)
    #shutil.copy(sharppeak_trace_fname, trace_fname)

