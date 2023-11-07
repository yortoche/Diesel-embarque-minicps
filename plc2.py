"""
Navy plc2
"""
from minicps.devices import Tank
from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import PLC_SAMPLES, PLC_PERIOD_SEC
from utils import IP

import time
import math

PLC1_ADDR = IP['plc1']
PLC2_ADDR = IP['plc2']

T201_2 = ('T201', 2)
P201_2 = ('P201', 2)

count = 0

class SwatPLC2(PLC):

    def pre_loop(self, sleep=0.1):

        print('DEBUG: pre_loop')
        time.sleep(sleep)

    def main_loop(self):

        print('DEBUG: main_loop')
        count = 0

        while count <= PLC_SAMPLES:
            
            t201 = float(self.get(T201_2))            
            print('temperature du moteur :',t201)
            self.send(T201_2, t201, PLC2_ADDR)

            if t201>95 :
                # here we open the pump to aircool the motor
                self.set(P201_2, 1)
                self.send(P201_2, 1, PLC2_ADDR)

            elif t201<41 :
                # here we close the pump because the motor is enough cooled
                self.set(P201_2, 0)
                self.send(P201_2, 0, PLC2_ADDR)

            time.sleep(PLC_PERIOD_SEC)
            count += 1


if __name__ == "__main__":

    # notice that memory init is different form disk init
    plc2 = SwatPLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)