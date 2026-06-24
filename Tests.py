import sys
import time
import pyvisa
from colorama import init, Fore, Back, Style
import numpy as np
init(autoreset=True)

def Initial_Start_Up_Test( DMM: str, PS: str,
    INITIAL_START_UP_VOLTAGE: float, INITIAL_START_UP_CURRENT: [float,float]) -> bool:
    '''4.2.1 DCDC CONVERTER DOC'''
    PS.write("INST CH1")
    PS.write("VOLT 5")
    PS.write("CURR 1")
    PS.write("OUTP ON")

    PS.query("*OPC?")   #checks if the power supply is all correct

    sample = []         #actual sampling process, avg 10 samps in 1 sec
    for i in range(10):
        sample.append(float(DMM.query("READ?")))
        time.sleep(0.1)

    test_result = round(np.mean(sample),2)

    print(sample)
    print(test_result)

    return test_result == INITIAL_START_UP_VOLTAGE

def Input_Voltage_Sweep(DMM: str, PS: str,
    VOLTAGE_SWEEP_RNG: [float,float]) -> bool:
    '''4.2.2 DCDC CONVERTER DOC'''

    PS.write("INST CH1")
    PS.write("CURR 1")
    PS.write("VOLT " + str(VOLTAGE_SWEEP_RNG[0]))
    sample = []
    #takes 10 tests in the same manner as prior test, each takes 1 second
    voltage= VOLTAGE_SWEEP_RNG[0]
    for i in range(10):
        sub_sample = []
        for j in range(10):
            sub_sample.append(float(DMM.query("READ?")))
            time.sleep(0.1)
            voltage = voltage + 0.002
            PS.write("VOLT " + str(voltage))
        sub_sample = round(np.mean(sub_sample),3)
        sample.append(sub_sample)
        print(sub_sample)
        time.sleep(0)


    return True