from gnuradio import gr
import numpy as np

import os
import sys
sys.path.append(os.getcwd())
import importlib

import pmt

non_module_func_printed=False
def non_module_func_body():
    global non_module_func_printed
    if not non_module_func_printed:
        print(f"NO EXPORT MODULE SELECTED")
        non_module_func_printed=True

def non_export_data(data):
    non_module_func_body()

def non_handle_async_msg(msg):
    non_module_func_body()

class PythonExportBlock(gr.sync_block):
    def __init__(self, exportmodulename=None, samp_rate=-1):
        gr.sync_block.__init__(
            self,
            name="PythonExportBlock",
            in_sig=[np.float32],
            out_sig=None
        )
        self.message_port_register_in(pmt.intern('msg_in'))
        self.message_port_register_out(pmt.intern("cmd_out"))

        #self.exportmodulename = exportmodulename
        if (exportmodulename is None):
            self.exportmodule = None
            self.process_data_func = non_export_data
            self.handle_async_msg_func = non_handle_async_msg
        else:
            self.exportmodule = importlib.import_module(exportmodulename)
            (getattr(self.exportmodule, "init"))(samp_rate)
            self.process_data_func = getattr(self.exportmodule, "export_data")
            self.handle_async_msg_func = getattr(self.exportmodule, "handle_async_msg")
            setattr(self.exportmodule, "send_async_msg_fn", self.send_cmd)

        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

    def handle_msg(self, msg):
        return self.handle_async_msg_func(msg)

    def send_cmd(self, msg):
        return message_port_pub(pmt.intern("cmd_out"), msg)

    def work(self, input_items, output_items):
        data = input_items[0]        
        #print(len(data))
        self.process_data_func(data)
        #print(data[:10])  # do whatever you want
        return len(data)

