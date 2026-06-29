import time

from colorama import init, Fore, Back, Style
import pyvisa
import numpy as np
from pyvisa import Resource


def DUNE_ASCII():
    print(Fore.MAGENTA +" ▄▄▄▄▄▄   ▄▄▄  ▄▄▄ ▄▄▄    ▄▄▄  ▄▄▄▄▄▄▄\n",
    Fore.MAGENTA +"███▀▀██▄ ███  ███ ████▄  ███ ███▀▀▀▀▀\n",
    Fore.MAGENTA +"███  ███ ███  ███ ███▀██▄███ ███▄▄\n",
    Fore.MAGENTA +"███  ███ ███▄▄███ ███  ▀████ ███\n",
    Fore.MAGENTA +"██████▀  ▀██████▀ ███    ███ ▀███████\n",
    Fore.MAGENTA +"DEEP UNDERGROUND NEUTRINO EXPERIMENT")

def IOV_Step_Funtion(DMM:Resource, PS:Resource, CALIBRATED_VOLTAGE_IN:float)->None:
    '''Steps the voltage fast'''
    DMM.write("*RST")
    PS.write("*RST")
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    DMM.write("*RST")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 10, "defbuffer1"')

    DMM.write('FUNC "VOLT:DC"')
    DMM.write('VOLT:DC:NPLC 0.01')
    DMM.write('ZERO:AUTO OFF')

    DMM.write('TRIG:LOAD "DurationLoop",1')
    DMM.write('TRIG:TIM 0.1')
    DMM.write('TRIG:COUN 10')

    time.sleep(2)  # wait before starting acquisition
    DMM.write('INIT')
    DMM.query('*OPC?')  # wait until complete

    data = DMM.query('TRAC:DATA? 1,10,"defbuffer1",READ')
    print(data)