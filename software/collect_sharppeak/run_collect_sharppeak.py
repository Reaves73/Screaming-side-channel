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


def start_qapp():
    qapp = Qt.QApplication(sys.argv)
    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    qapp.exec_()

def stop_qapp():
    Qt.QApplication.quit()
        

def start_qapp_async():
    threading.Thread(target=start_qapp, daemon=True).start()


def control_server(host="127.0.0.1", port=9999):
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
                print("Starting qapp")
                start_qapp_async()
                tb = collect_sharppeak()
                tb.start()
                set_recording(tb, True)
                time.sleep(0.3)
                set_recording(tb, False)
                tb.stop()
                tb.wait()
                print("Stopping qapp")
                stop_qapp()
                
                conn.sendall(b"OK START\n")
            elif data == "0":
                break
            else:
                conn.sendall(b"UNKNOWN CMD\n")
        except Exception as e:
            print("socket error:", e)
        finally:
            conn.close()


if __name__ == "__main__":
    control_server()
