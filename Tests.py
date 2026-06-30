import sys
import time
import pyvisa
import winsound
from colorama import init, Fore, Back, Style
import numpy as np
from pyvisa import Resource
import matplotlib.pyplot as mp

debug = True #general debug to see more test output
debug_nstab = True
init(autoreset=True)

def Calibrate_to_Ideal_Incoming_Voltage(  DMM: Resource, PS: Resource, IDEAL_INCOMING_VOLTAGE: float,
                                        CALIBRATED_VOLTAGE_IN: float) -> (float,float):
    '''Makes minimal adjustments to get incoming voltage to 5 volts with up to 0.01 VOLT error'''
    #reset calibrated voltage
    CALIBRATED_VOLTAGE_IN = 5.0
    PS.write("INST CH1")
    PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")
    #now its on, make adj if not in range
    PS.query("*OPC?")
    time.sleep(0.3)

    DMM.write("ROUT:MULT:CLOS (@1)")

    incoming_volts = float(DMM.query("READ?"))

    if debug:
        print(incoming_volts)
    else:
        print("CALIBRATING INPUT VOLTAGE...")
    start_time = time.time()
    #this will try and calibrate voltage
    tolerance = 0.01 #tolerance in volts
    Calibration_Timeout = 400
    while abs(incoming_volts - IDEAL_INCOMING_VOLTAGE) > tolerance:
        #throws an error and safely shuts down upon time out
        if Calibration_Timeout <=0:
            DMM.write("*RST")
            PS.write("*RST")
            final_time = round(time.time() - start_time, 3)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            sys.exit("CALIBRATION FAILED DUE TO TIMEOUT AT " + str(final_time) + " SEC.")
        #this is a stupid visual display to make sure people know its doing something
        if debug:
            print(CALIBRATED_VOLTAGE_IN)
            print("error of " + str(abs(incoming_volts - IDEAL_INCOMING_VOLTAGE)))

        if (incoming_volts - IDEAL_INCOMING_VOLTAGE) >= tolerance:
            CALIBRATED_VOLTAGE_IN -=0.00012*IDEAL_INCOMING_VOLTAGE
        if (incoming_volts - IDEAL_INCOMING_VOLTAGE) <= -tolerance:
            CALIBRATED_VOLTAGE_IN +=0.00012*IDEAL_INCOMING_VOLTAGE
        PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
        PS.query("*OPC?")
        time.sleep(0.05)

        incoming_volts = float(DMM.query("READ?"))
        Calibration_Timeout -=1

    if debug:
        print("final input v of " + str(CALIBRATED_VOLTAGE_IN) + " which gives board input of " + str(incoming_volts))
        final_time = round(time.time() - start_time,3)
        print(Back.LIGHTCYAN_EX + Fore.BLACK + str(final_time) + " sec. elapsed in calibration")
    else:
        print("INPUT VOLTAGE CALIBRATED TO " + Fore.GREEN + str(round(CALIBRATED_VOLTAGE_IN,5)), "VOLTS")
    DMM.write("*RST")
    return CALIBRATED_VOLTAGE_IN, incoming_volts

def Initial_Start_Up_Test( DMM: Resource, PS: Resource,
                            INITIAL_START_UP_VOLTAGE: list[float], INITIAL_START_UP_CURRENT: list[float],
                            CALIBRATED_VOLTAGE_IN:float, test_output) -> bool:
    '''4.2.1 DCDC CONVERTER DOC'''
    #NOW UPDATED FOR MULTICHANNEL DMM BOARDS ONLY
    PS.write("INST CH1")
    PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")

    PS.query("*OPC?")   #checks if the power supply is all correct

    time.sleep(0.3) ####ASK MIKE ABOUT THIS STARTUP DELAY, SHOULD IT BE INSTANT?

    sample_volts = []         #actual sampling process on ch3, avg 10 samps in 1 sec
    DMM.write("ROUT:MULT:CLOS (@3)")
    for i in range(10):
        sample_volts.append(float(DMM.query("READ?")))
        time.sleep(0.1)
    DMM.write("ROUT:MULT:OPEN (@3)")

    sample_mamps = []  # same proc on ch 2 for current
    DMM.write("ROUT:MULT:CLOS (@2)")
    for i in range(10):
        sample_mamps.append(float(DMM.query("READ?")))
        time.sleep(0.1)
    DMM.write("ROUT:MULT:OPEN (@2)")

    test_result = round(np.mean(sample_volts),3)
    test_result2 = round(np.mean(sample_mamps),3)
    if debug:
        print("voltage debug results:")
        print(sample_volts)
        print(test_result)
        print("current debug results:")
        print(sample_mamps)
        print(test_result2)

    #append to df
    test_output["initial_voltage"] = test_result
    test_output["initial_current"] = test_result2
    if (test_result <= INITIAL_START_UP_VOLTAGE[1] and test_result >= INITIAL_START_UP_VOLTAGE[0]
            and test_result2 <= INITIAL_START_UP_CURRENT[1] and test_result2 >= INITIAL_START_UP_CURRENT[0]):
        test_output["initial_start_up"] = "PASS"
        return True
    test_output["initial_start_up"] = "FAIL"
    return False

def Input_Voltage_Sweep(DMM: Resource, PS: Resource, INITIAL_START_UP_VOLTAGE: list[float],
                        CALIBRATED_VOLTAGE_IN:float, test_output) -> bool:
    '''4.2.2 DCDC CONVERTER DOC'''

    #sets lower bound of calibrated voltage
    voltage = CALIBRATED_VOLTAGE_IN-0.1
    PS.write("INST CH1")
    PS.write("VOLT " + str(voltage))
    PS.query("*OPC?")

    sample = []
    DMM.write("ROUT:MULT:CLOS (@3)")

    for i in range(10):
        sub_sample = []

        for j in range(10):
            sub_sample.append(float(DMM.query("READ?")))
            time.sleep(0.05)
            voltage += 0.2/100
            PS.write("VOLT " + str(voltage))

        mean_val = round(np.mean(sub_sample), 3)
        sample.append(mean_val)

        if debug:
            print(mean_val)
    #close channel and then run comps
    DMM.write("ROUT:MULT:CLOS (@3)")
    for i in range(10):
        mean_val = sample[i]
        if mean_val <= INITIAL_START_UP_VOLTAGE[0] or mean_val >= INITIAL_START_UP_VOLTAGE[1]:
            test_output["input_voltage_sweep"] = "FAIL"
            return False

    test_output["input_voltage_sweep"] = "PASS"
    return True

def Nominal_Load_Performance(DMM: Resource, PS: Resource, INITIAL_START_UP_VOLTAGE: list[float],
                        CALIBRATED_VOLTAGE_IN:float, test_output, nstab_test_output) -> bool:
    '''4.2.3 DCDC CONVERTER DOC'''
    #this tells the meter to make 10 measurements at 100ms incr, and then save and return them to me
    #with execution upon prompting
    DMM.write("*RST")
    DMM.write("ROUT:MULT:CLOS (@3)")

    #activates relay for 1 megaohn resistance channel
    #that is, channel 2
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")
    time.sleep(0.3)
    PS.write("INST CH2")
    PS.write("VOLT 5")
    PS.write("CURR 0.200")
    PS.write("OUTP ON")
    PS.query("*OPC?")  # checks both channels to be correct
    time.sleep(0.3)

    final_output = None
    #readback data and then unpack
    if debug_nstab:
        #strangely behaving here
        '''Steps the voltage fast'''
        DMM.write("*RST")
        PS.write("*RST")
        PS.write("INST CH1")
        PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
        DMM.write("*RST")
        DMM.write('TRAC:CLE "defbuffer1"')
        DMM.write('TRAC:POIN 10, "defbuffer1"')
        print("buffer set")

        DMM.write('FUNC "VOLT:DC"')
        print("idk")
        DMM.write('VOLT:DC:NPLC 0.01')
        DMM.write('ZERO:AUTO OFF')
        print("auto zering")

        DMM.write('TRIG:LOAD "DurationLoop",1')
        DMM.write('TRIG:TIM 0.1')
        DMM.write('TRIG:COUN 10')

        time.sleep(2)  # wait before starting acquisition
        DMM.write('INIT')
        DMM.query('*OPC?')  # wait until complete

        data = DMM.query('TRAC:DATA? 1,10,"defbuffer1",READ')
        print(data)

    else:
        final_output = float(DMM.query("READ?"))

    if debug: print(str(final_output) + " was final stabilized voltage")
    if final_output >= INITIAL_START_UP_VOLTAGE[0] and final_output <= INITIAL_START_UP_VOLTAGE[1]:
        test_output["nominal_load_performance"] = "PASS"
        return True
    else:
        test_output["nominal_load_performance"] = "FAIL"
        return False

def Input_and_Ouput_Cold( DMM: Resource, PS: Resource,OUTPUT_VOLTAGE: float, INPUT_CURRENT:float,
                          test_ouput) -> bool:
    '''4.3.2'''
    return True

def Input_Voltage_Step(DMM: Resource, PS: Resource, CALIBRATED_VOLTAGE_IN: float):

    DMM.write("*RST")
    PS.write("*RST")
    PS.write("INST CH1")
    PS.write("VOLT 5")
    PS.write("CURR 0.05")
    PS.write("OUTP ON")
    time.sleep(3)
    PS.query("*OPC?")
    #calibrates inputs

    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02')
    #go ahead and take 100 measurements in 2 sec
    DMM.write('INIT')
    time.sleep(0.5)

    PS.write("VOLT 5.1")

    #let me know when done, will throw all sorts of errors if something in the setup isnt perfect
    DMM.query('*OPC?')

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    print("samples:", n)

    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        print(datalist)
        #mangled scipi formatting, had to do it manually
        datalist = [round(float(datalist[i][:datalist[i].index("E")])*10**int(datalist[i][datalist[i].index("E")+1:]),5)
                    for i in range(len(datalist))]
        mp.plot(datalist)
        mp.show()