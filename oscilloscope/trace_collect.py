import os
import time
import pyvisa
import numpy as np

IP = "169.254.41.7"
PORT = 5025


# Connect
def connect_scope(ip: str, port: int = 5025):
    rm = pyvisa.ResourceManager("@py")
    scope = rm.open_resource(f"TCPIP::{ip}::{port}::SOCKET")
    scope.read_termination = "\n"
    scope.write_termination = "\n"
    scope.timeout = 50000  
    print("IDN:", scope.query("*IDN?").strip())
    scope.write("*CLS")
    return rm, scope



# Osci intial setup
def setup_scope(scope):
    scope.write("*RST")
    scope.query("*OPC?")
    scope.write("*CLS")
    print("reset finish")

    # CH1 set
    scope.write(":CHAN1:STATe ON")
    scope.write(":CHAN1:SCAL 0.5")
    scope.write(":CHAN1:OFFS 0")

    # CH2 set , CH2 read power from MCU
    scope.write(":CHAN2:STATe ON")
    scope.write(":CHAN2:SCAL 0.01")
    scope.write(":CHAN2:OFFS -0.555")

    # intial trigger CH 1 normal mode and rasing edge trigger
    scope.write(":TRIGger:MODE NORMal")
    scope.write(":TRIG:EVEN1:SOUR CHANNEL1")
    scope.write(":TRIGger:EVENt1:EDGE:SLOPe POSitive")
    scope.write(":TRIG:EVEN1:LEV -1.7")  

    # set the sampling duration
    scope.write(":TIM:SCAL 0.002")
    scope.write(":TIM:POSITION 0.0036")

    # float32, read power voltage from CH2
    scope.write("FORMat:DATA REAL,32")
    #scope.write("EXPort:WAVeform:SOURce C1")
    scope.write("EXPort:WAVeform:SOURce C2")
    scope.write("EXPort:WAVeform:SCOPe DISP")



# Capture one trace
def acquire_one(scope) -> np.ndarray:
    scope.write("*CLS")
    scope.write(":SING")

    # Wait for the trigger
    scope.query("*OPC?")
    print("trigger come")

    # 
    scope.write("EXPort:WAVeform:DATA:VALues?")
    y = scope.read_binary_values(datatype="f", container=np.array)
    return y



# Loop and save
def collect_loop(scope, n_traces: int, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    for i in range(n_traces):
        
        y = acquire_one(scope)

        # save
        np.save(os.path.join(out_dir, f"trace_{i:06d}.npy"), y)

        #if i % 20 == 0:
        print(f"[{i}/{n_traces}] saved, points={y.size}")


def main():
    rm, scope = connect_scope(IP, PORT)
    try:
        setup_scope(scope)
        collect_loop(scope, n_traces=100, out_dir="traces_mxo5")
        print("finish")
    finally:
        try:
            scope.close()
        finally:
            rm.close()


if __name__ == "__main__":
    main()