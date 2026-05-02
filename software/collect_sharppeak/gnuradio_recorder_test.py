import sys
import time
import signal
import socket
import threading
import shutil
import os

n_traces = 5
tracesdir = (os.getcwd()) + "/traces"
os.makedirs(tracesdir, exist_ok=True)
traces_fname_prefix = f"{tracesdir}/tr_"

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

