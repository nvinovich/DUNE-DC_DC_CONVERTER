import sys
import time
import pyvisa
from colorama import init, Fore, Back, Style
import numpy as np
from pyvisa import Resource

debug = False #general debug to see more test output
init(autoreset=True)

def Initial_Start_Up_Test( DMM: Resource, PS: Resource,
    INITIAL_START_UP_VOLTAGE: list[float], INITIAL_START_UP_CURRENT: list[float],
                           test_output) -> bool:
    '''4.2.1 DCDC CONVERTER DOC'''
    PS.write("INST CH1")
    PS.write("VOLT 5")
    PS.write("CURR 0.034")
    PS.write("OUTP ON")

    PS.query("*OPC?")   #checks if the power supply is all correct

    sample = []         #actual sampling process, avg 10 samps in 1 sec
    for i in range(10):
        sample.append(float(DMM.query("READ?")))
        time.sleep(0.1)

    test_result = round(np.mean(sample),3)
    if debug:
        print(sample)
        print(test_result)

    #append to df
    test_output["initial_voltage"] = test_result
    if test_result <= INITIAL_START_UP_CURRENT[1] and test_result >= INITIAL_START_UP_CURRENT[0]:
        test_output["initial_start_up"] = "PASS"
        return True
    test_output["initial_start_up"] = "FAIL"
    return False

def Input_Voltage_Sweep(DMM: Resource, PS: Resource,
    VOLTAGE_SWEEP_RNG: list[float], INITIAL_START_UP_VOLTAGE: list[float],
                        test_output) -> bool:
    '''4.2.2 DCDC CONVERTER DOC'''
    PS.write("INST CH1")

    voltage = VOLTAGE_SWEEP_RNG[0]
    PS.write("VOLT " + str(voltage))

    sample = []
    low, high = INITIAL_START_UP_VOLTAGE

    for i in range(10):
        sub_sample = []

        for j in range(10):
            sub_sample.append(float(DMM.query("READ?")))
            time.sleep(0.05)
            voltage += 0.002
            PS.write("VOLT " + str(voltage))

        mean_val = round(np.mean(sub_sample), 3)
        sample.append(mean_val)

        if debug:
            print(mean_val)
    for i in range(10):
        mean_val = sample[i]
        if mean_val < low or mean_val > high:
            test_output["input_voltage_sweep"] = "FAIL"
            return False

    test_output["input_voltage_sweep"] = "PASS"
    return True