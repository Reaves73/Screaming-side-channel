#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import signal
import socket
import threading
from PyQt5 import Qt

from collect_sharppeak import collect_sharppeak


def set_recording(tb, enabled):
    if enabled:
        tb.blocks_selector_0.set_output_index(1)   # to File Sink
        print("save")
    else:
        tb.blocks_selector_0.set_output_index(0)   # to Null Sink
        print("stop save")


def control_server(tb, host="127.0.0.1", port=9999):
    #open a server to listen
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    print(f"listening on {host}:{port}")
    print("send 1 to start saving, send 0 to stop saving")

    while True:
        conn, addr = s.accept()
        try:
            data = conn.recv(1024).decode().strip()
            print(f"received: {data} from {addr}")

            if data == "1":
                set_recording(tb, True)
                conn.sendall(b"OK START\n")
            elif data == "0":
                set_recording(tb, False)
                conn.sendall(b"OK STOP\n")
            else:
                conn.sendall(b"UNKNOWN CMD\n")
        except Exception as e:
            print("socket error:", e)
        finally:
            conn.close()


def main():
    qapp = Qt.QApplication(sys.argv)

    tb = collect_sharppeak()

    #start running and show gui
    tb.start()
    tb.show()

    set_recording(tb, False) #not save by default

    threading.Thread(target=control_server, args=(tb,), daemon=True).start()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()


if __name__ == "__main__":
    main()