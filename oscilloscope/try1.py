import pyvisa
import numpy as np
 
 
 
def print_stat(scope):
              print(scope.query("*IDN?"))
              print("Error:", scope.query(":SYST:ERR?"))
              #print("ACQ state:", scope.query(":ACQ:STATE?"))      # must be 0
              #print("TRIG state:", scope.query(":TRIG:STAT?"))     # must be STOP
              #print("WAV points:", scope.query(":WAV:POIN?"))      # must be > 0
              #print("WAV mode:", scope.query(":WAV:MODE?"))        # must be RAW or NORM
              #print("WAV source:", scope.query(":WAV:SOUR?"))      # must be CHAN1
              #print("CHAN1 disp:", scope.query(":CHAN1:DISP?"))    # must be 1
 
# -----------------------
# 1) Connect to scope
# -----------------------
IP = "169.254.41.7"
rm = pyvisa.ResourceManager("@py")   # use pyvisa-py backend
scope = rm.open_resource(f"TCPIP::{IP}::5025::SOCKET")
 
scope.timeout = 10000  # 30s, increase if needed
scope.read_termination = "\n"
scope.write_termination = "\n"
 
print("IDN:", scope.query("*IDN?"))
 
# Clear errors
scope.write("*RST")
print("RSTError:", scope.query(":SYST:ERR?"))
scope.write("*CLS")
print("CLSError:", scope.query(":SYST:ERR?"))
 
# -----------------------
# 2) Channel 1 settings
# -----------------------
scope.write(":CHAN1:STATe ON")     # turn on channel 1
scope.write(":CHAN1:SCAL 0.5")    # volts/div (adjust as needed)
scope.write(":CHAN1:OFFS 0")      # vertical offset
print_stat(scope)
 
# -----------------------
# 3) Trigger settings
# -----------------------
scope.write(":TRIGger:MEVents:MODE SINGle")
scope.write(":TRIG:EVEN1:SOUR CHANNEL1")        # edge trigger
#scope.write(":TRIG:A:SOUR CHAN1")       # trigger source = channel 1
#scope.write(":TRIG:A:EDGE:SLOP POS")    # rising edge
#scope.write(":TRIG:A:LEV 0")            # 0 V trigger level
#scope.write(":TRIG:A:MODE NORM")        # normal trigger mode
 
scope.write(":CHAN1:SCAL 0.005")        # normal trigger mode
print_stat(scope)
 
# -----------------------
# 4) Timebase
# -----------------------
scope.write(":TIM:SCAL 0.0005")  # 10 ms/div, adjust total capture length
print_stat(scope)
 
# -----------------------
# 5) Single acquisition
# -----------------------
scope.write(":SING")          # arm single acquisition
#scope.write(":TRIG:FORCE")        # force trigger immediately
print("OPC: ", scope.query("*OPC?"))          # wait until acquisition completes
print_stat(scope)
 
# -----------------------
# 6) Waveform setup
# -----------------------
scope.write(":EXPort:WAVeform:SOUR C1")    # select channel 1
print_stat(scope)
 
 
scope.write(":EXPort:WAVeform:DATA:HEADer")
 
 
"""
# -----------------------
# 7) Read scaling
# -----------------------
xinc = float(scope.query(":WAV:XINC?"))
xorg = float(scope.query(":WAV:XOR?"))
yinc = float(scope.query(":WAV:YINC?"))
yorg = float(scope.query(":WAV:YOR?"))
print_stat(scope)
 
 
 
# -----------------------
# 8) Read waveform
# -----------------------
raw = scope.query_binary_values(":WAV:DATA?", datatype='B', container=np.array)
time = xorg + np.arange(len(raw)) * xinc
voltage = yorg + raw * yinc
 
# -----------------------
# 9) Save CSV
# -----------------------
np.savetxt("trace_ch1.csv", np.column_stack((time, voltage)),
           delimiter=",", header="time_s,voltage_V", comments="")
"""
scope.write("FORMat:DATA REAL,32")
scope.write("EXPort:WAVeform:SOURce C1")
scope.write("EXPort:WAVeform:SCOPe DISP")
scope.write("EXPort:WAVeform:DATA:VALues?")
raw = scope.read_binary_values(
    datatype="f",
    container=np.array
)
raw.tofile("C1.bin")
scope.close()
print("Trace saved as trace_ch1.csv")