import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/lib")

import sharpcapturer

import matplotlib.pyplot as plt
import numpy as np

config_dict = {} 
config_dict["experiment_name"] = "testexp"

#config_dict["PLATFORM"] = "CW308_STM32F0"
config_dict["PLATFORM"] = "CW308_STM32F3"

config_dict["n_traces"] = 5
#config_dict["n_traces"] = 50
#config_dict["n_traces"] = 5000

config_dict["include_trace_chipwhisperer"] = True
config_dict["include_trace_gnuradio"] = True

config_dict["chipwhisperer_n_samples"] = 12000
#config_dict["chipwhisperer_n_samples"] = 24000

config_dict["chipwhisperer_n_decimate"] = 1
#config_dict["chipwhisperer_n_decimate"] = 4

sharpcapturer.capture(config_dict)


#plt.plot(np.average(traces, axis=0))
##plt.plot(avg)
##yuqi_try: draw line of trigger.
##plt.axvline(x=0, color='red', linewidth=1)
#
#plt.show()
