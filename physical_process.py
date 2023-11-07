from http.client import TEMPORARY_REDIRECT
from pipes import Template
from minicps.devices import Tank

from utils import PUMP_FLOWRATE_IN, PUMP_FLOWRATE_OUT
from utils import TANK_HEIGHT, TANK_SECTION, TANK_DIAMETER
from utils import LIT_101_M, RWT_INIT_LEVEL
from utils import STATE, PP_PERIOD_SEC, PP_PERIOD_HOURS, PP_SAMPLES
import pandas as pd

import sys
import time
import math

MV101 = ('MV101', 1)
P201 = ('P201', 2)
LIT101 = ('LIT101', 1)
LIT301 = ('LIT301', 3)
FIT101 = ('FIT101', 1)
FIT201 = ('FIT201', 2)
T201 = ('T201', 2)

count=0

class RawWaterTank(Tank):

    def pre_loop(self):

        print('DEBUG: pre_loop')
        self.T0 = 25  # Température initiale en °C
        self.k1 = 0.0008  # Constante de temps réchauffage
        self.k2 = 0.05  # constante refroidissement
        self.Tmax = 120  # Température maximale en °C
        self.Tf = 40  # Température de stabilisation de la température du moteur si la pompe est activée à l'infini
        self.set(LIT101, 0.200)

        self.set(MV101, 0)
        self.set(P201, 0)
        self.time_since_pump_on = 0  # Temps depuis que la pompe a été activée, variable qui existe pour les besoins du code
        temp = self.T0

    def main_loop(self):

        print('DEBUG: main_loop')
        count = 0
        timestamp=0
        temp = self.T0

        while(count <= PP_SAMPLES): #pp samples a été préalablement défini dans utils

            p201=int(self.get(P201))
            print('etat de la pompe :', p201)
            mv101=int(self.get(MV101))
            print('etat de la vanne :', mv101)
            lit101=float(self.get(LIT101))
            print('niveau d eau', lit101)

            new_level = lit101
            water_volume = self.section * new_level

            if (p201 == 0): #pompe fermee donc il n'y a pas de refroidissement
                temp += (self.Tmax - temp) * (1 - math.exp(-self.k1 * count)) # FORMULE SANS REFROIDISSEMENT
                self.set(T201,temp) # donne la nouvelle température moteur
                self.time_since_pump_on = 0  # Réinitialiser le temps depuis que la pompe a été activée

                if (mv101 == 1): #pompe fermee donc le niveau d'eau ne change que si la vanne est ouverte
                    self.set(FIT101, PUMP_FLOWRATE_IN)
                    inflow = PUMP_FLOWRATE_IN * PP_PERIOD_HOURS
                    water_volume += inflow
                    print("volume de la cuve :", water_volume)

            elif (p201 == 1):  # pompe ouverte donc on démarre le refroidissement.
                Ti = temp
                cooling_effect = (Ti - self.Tf) * (1 - math.exp(-self.k2 * self.time_since_pump_on))
                temp = max(Ti - cooling_effect, self.Tf)
                self.set(T201,temp)
                self.time_since_pump_on += 1  # Augmenter le temps depuis que la pompe a été activée

                if (mv101 == 1): # la pompe est ouverte ce qui vide la cuve mais la vanne est ouverte ce qui remplit la cuve
                    self.set(FIT101, PUMP_FLOWRATE_IN)
                    self.set(FIT201, PUMP_FLOWRATE_OUT)
                    inflow = (PUMP_FLOWRATE_IN - PUMP_FLOWRATE_OUT) * PP_PERIOD_HOURS
                    water_volume += inflow

                elif (mv101 == 0): #seule la pompe est ouverte, la cuve se vide sans se remplir
                    self.set(FIT201, PUMP_FLOWRATE_OUT)
                    outflow = PUMP_FLOWRATE_OUT * PP_PERIOD_HOURS
                    water_volume -= outflow

            print('temperature du moteur :', temp)
            print('volume de la cuve :', water_volume)
            section = self.section
            lit101 = water_volume / section
            self.set(LIT101, lit101)
            self.set(T201,temp)

            count += 1
            time.sleep(PP_PERIOD_SEC)
            timestamp+=PP_PERIOD_SEC

if __name__ == '__main__':

    rwt = RawWaterTank(
        name='rwt',
        state=STATE,
        protocol=None,
        section=TANK_SECTION,
        level=RWT_INIT_LEVEL
    )