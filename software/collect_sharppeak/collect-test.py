import sys
import time
import signal
import socket
import threading
import shutil


n_traces = 5
traces_fname_prefix = "traces/tr_"
sharppeak_trace_fname = "/home/lindnera/data/TestSharpWhisperer/software/cw-code/data_sharppeak/sharppeak"


def send_trigger(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9999))
    s.sendall(cmd.encode())
    s.close()
    return


#
# CAPTURE
#

print("Capturing traces...")

for i in range(n_traces):
    print("Trace", i)
    
    send_trigger("1")
    time.sleep(1.5)
    trace_fname = f"{traces_fname_prefix}{i}.bin"
    shutil.copy(sharppeak_trace_fname, trace_fname)

send_trigger("0")
