# MIT License

# Copyright (c) 2024 Can Aknesil
# Copyright (c) 2025 Can Aknesil

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import chipwhisperer as cw
import time


class CWHardware:
    # from Setup_Generic.ipynb
    def connect(self, platform):
        PLATFORM = platform
        
        scope = cw.scope()
        
        try:
            target = cw.target(scope)
        except IOError:
            print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
            print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
            scope = cw.scope()
            target = cw.target(scope)
        
        print("INFO: Found ChipWhisperer😍")
        
        if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
            prog = cw.programmers.STM32FProgrammer
        elif PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
            prog = cw.programmers.XMEGAProgrammer
        else:
            prog = None

        self.scope = scope
        self.target = target
        self.target_programmer = prog
        self.platform = PLATFORM
                
        time.sleep(0.05)
        return True
    
    
    def reset_target(self):
        PLATFORM = self.platform
        scope = self.scope
        
        if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
            scope.io.pdic = 'low'
            time.sleep(0.05)
            scope.io.pdic = 'high_z' #XMEGA doesn't like pdic driven high
            time.sleep(0.05)
        else:  
            scope.io.nrst = 'low'
            time.sleep(0.05)
            scope.io.nrst = 'high'
            time.sleep(0.05)

        return True
        
    
    def program_target(self, fw_path):
        scope = self.scope
        prog = self.target_programmer
        
        # from PA_CPA_1-Using_CW-Analyzer_for_CPA_Attack.ipynb
        cw.program_target(scope, prog, fw_path)
        time.sleep(1)
        return True

    
    def disconnect(self):
        self.scope.dis()
        self.target.dis()

        
    def arm(self):
        self.scope.arm()
        
    def capture(self, text, key):
        ret = cw.capture_trace(self.scope, self.target, text, key)
        return ret
        #self.target.simpleserial_write('p', text)

        #self.arm()

        #ret = self.scope.capture()
        #if ret is None:
        #    return None, None

        #trace = self.scope.get_last_trace()
        #response = self.target.simpleserial_read('r', 16)
    
        #return response, trace


