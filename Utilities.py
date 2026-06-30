import sys
import time

from colorama import init, Fore, Back, Style
import pyvisa
import numpy as np
from pyvisa import Resource

from Tests import Input_Voltage_Step


def DUNE_ASCII():
    print(Fore.MAGENTA +" ▄▄▄▄▄▄   ▄▄▄  ▄▄▄ ▄▄▄    ▄▄▄  ▄▄▄▄▄▄▄\n",
    Fore.MAGENTA +"███▀▀██▄ ███  ███ ████▄  ███ ███▀▀▀▀▀\n",
    Fore.MAGENTA +"███  ███ ███  ███ ███▀██▄███ ███▄▄\n",
    Fore.MAGENTA +"███  ███ ███▄▄███ ███  ▀████ ███\n",
    Fore.MAGENTA +"██████▀  ▀██████▀ ███    ███ ▀███████\n",
    Fore.MAGENTA +"DEEP UNDERGROUND NEUTRINO EXPERIMENT")

def RESOURCE_CONNECTOR(RM)->(Resource,Resource):
    '''CONNECTS DMM THEN PS'''
    print("Checking for resources...")
    resources = RM.list_resources()

    if len(resources) == 0:
        sys.exit("No resources found.")

    DMM = None
    PS = None

    for r in resources:
        try:
            device = RM.open_resource(r)

            device.timeout = 5000
            device.read_termination = "\n"
            device.write_termination = "\n"

            device.clear()
            device.write("*CLS")
            device.write("*RST")

            idn = device.query("*IDN?").strip()
            manufacturer, model, serial, firmware = idn.split(",")

            if model == "MODEL DMM6500":
                DMM = device
                print(Fore.MAGENTA+"DMM connected:", idn)

            elif model == "E36312A":
                PS = device
                print(Fore.MAGENTA+"PS connected:", idn)
        except Exception:
            continue

    if DMM is None:
        sys.exit("No digital multimeter found.")
    if PS is None:
        sys.exit("No power supply found.")

    return DMM, PS

if __name__ =='__main__':
    #just a debug script for the data buffer proc
    RM = pyvisa.ResourceManager()
    DMM, PS = RESOURCE_CONNECTOR(RM)

    Input_Voltage_Step(DMM, PS,5)

    RM.close()