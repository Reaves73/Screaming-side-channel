from gnuradio import gr
import numpy as np

import os
import sys
#print(f"cwd: {os.getcwd()}")
#sys.path.append("/home/lindnera/data/SharpWhisperer/software/collect_sharppeak/recorder")
sys.path.append(os.getcwd())
import importlib
#import mygoodcode

non_exportdata_printed=False
def non_exportdata(data):
    global non_exportdata_printed
    if not non_exportdata_printed:
        print(f"NO EXPORT MODULE SELECTED")
        non_exportdata_printed=True

class PythonExportBlock(gr.sync_block):
    def __init__(self, exportmodulename=None):
        gr.sync_block.__init__(
            self,
            name="PythonExportBlock",
            in_sig=[np.float32],
            out_sig=None
        )
        #self.exportmodulename = exportmodulename
        if (exportmodulename is None):
            self.exportmodule = None
            self.processdata_func = non_exportdata
        else:
            self.exportmodule = importlib.import_module(exportmodulename)
            (getattr(self.exportmodule, "init"))()
            self.processdata_func = getattr(self.exportmodule, "exportdata")

    def work(self, input_items, output_items):
        data = input_items[0]        
        #print(len(data))
        #mygoodcode.processdata(data)
        self.processdata_func(data)
        #print(data[:10])  # do whatever you want
        return len(data)

