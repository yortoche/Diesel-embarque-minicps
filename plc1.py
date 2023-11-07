"""
Navy plc1.py
"""

from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import PLC_PERIOD_SEC, PLC_SAMPLES
from utils import IP, LIT_101_M, FIT_201_THRESH

import time

PLC1_ADDR = IP['plc1']
PLC2_ADDR = IP['plc2']

FIT101 = ('FIT101', 1)
MV101 = ('MV101', 1)
LIT101 = ('LIT101', 1)
# interlocks to be received from plc2
FIT201_1 = ('FIT201', 1)
FIT201_2 = ('FIT201', 2)
T201_1 = ('T201',1)
T201_2 = ('T201',2)
P201_1 = ('P201', 1)
P201_2 = ('P201', 2)

# TODO: real value tag where to read/write flow sensor
class SwatPLC1(PLC):

    def pre_loop(self, sleep=0.1):
        print('DEBUG: Navy plc1 enters pre_loop')
        time.sleep(sleep)

    def main_loop(self):
        print('DEBUG: Navy plc1 enters main_loop.')
        count = 0

        while(count <= PLC_SAMPLES):
            
            #les interlocks, provenant de plc2 :

            t201 = float(self.receive(T201_2, PLC2_ADDR))
            self.send(T201_1, t201, PLC1_ADDR)
            print('temperature du moteur', t201)
            p201 = int(self.receive(P201_2, PLC2_ADDR))
            self.send(P201_1, p201, PLC1_ADDR)
            print('etat de la pompe', p201)

            #les non interlocks :

            mv101 = int(self.get(MV101))
            print('etat de la vanne :', mv101)
            lit101 = float(self.get(LIT101))
            print('niveau d eau dans la cuve', lit101)

            if (p201==1):
                if (mv101==1):
                    print('ETAT : refroidissement moteur & remplissage cuve, donc TEMP decroit et LIT croit faiblement')
                elif (mv101==0):
                    print('ETAT : refroidissement moteur & cuve ne se remplit pas, donc TEMP decroit et LIT croit faiblement')
            elif (p201==0):
                if (mv101==1):
                    print('ETAT : pas de refroidissement moteur & remplissage cuve, donc TEMP croit et LIT croit fortement')
                elif (mv101==0):
                    print('ETAT : pas refroidissement moteur & cuve ne se remplit pas, donc TEMP decroit et LIT stagne')

            if lit101 >= LIT_101_M['HH']:
                # niveau d'eau trop haut donc on ferme la vanne
                print("WARNING PLC1 - lit101 over HH: %.2f >= %.2f." % (lit101, LIT_101_M['HH']))
                self.set(MV101, 0)
                self.send(MV101, 0, PLC1_ADDR)

            if lit101 >= LIT_101_M['H']:
                # niveau d'eau trop haut donc on ferme la vanne
                print("INFO PLC1 - lit101 over H -> close mv101.")
                self.set(MV101, 0)
                self.send(MV101, 0, PLC1_ADDR)

            elif lit101 <= LIT_101_M['LL']:
                # niveau d'eau trop bas donc on ouvre la vanne
                print("WARNING PLC1 - lit101 under LL: %.2f <= %.2f." % (lit101, LIT_101_M['LL']))
                self.set(MV101, 1)
                self.send(MV101, 1, PLC1_ADDR)

            elif lit101 <= LIT_101_M['L']:
                # niveau d'eau trop bas donc on ouvre la vanne
                print("INFO PLC1 - lit101 under L -> open mv101.")
                self.set(MV101, 1)
                self.send(MV101, 1, PLC1_ADDR)

            time.sleep(PLC_PERIOD_SEC)
            count += 1

if __name__ == "__main__":

    # notice that memory init is different form disk init
    plc1 = SwatPLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)