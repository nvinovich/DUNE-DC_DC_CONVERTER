import os
import time
from os.path import samefile

import pyvisa
import winsound
from colorama import init, Fore, Back, Style
from numpy.ma.extras import average

from Config import snd
from Utilities import Q_TIMER

init(autoreset=True)
import numpy as np
from pyvisa import Resource
import matplotlib.pyplot as mp
show_plots = False

#               !!! THIS IS THE BIG SCARY TESTING FILE, PLEASE DON'T MESS WITH  !!!

def Initial_Start_Up_Test( DMM: Resource, PS: Resource,
                            INITIAL_START_UP_VOLTAGE: list[float], INITIAL_START_UP_CURRENT: list[float],
                            CALIBRATED_VOLTAGE_IN:float, test_output, trace_ouput,debug:bool) -> bool:
    '''4.2.1 DCDC CONVERTER DOC'''
    #NOW UPDATED FOR MULTICHANNEL DMM BOARDS ONLY
    PS.write("INST CH1")
    PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")

    PS.query("*OPC?")   #checks if the power supply is all correct

    time.sleep(0.3) ####ASK MIKE README THIS STARTUP DELAY, SHOULD IT BE INSTANT?

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

    test_result = float(round(np.mean(sample_volts),3)) #fixed a minor parsing issue
    test_result2 = float(round(np.mean(sample_mamps),3))
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
            and test_result2 >= INITIAL_START_UP_CURRENT[1] and test_result2 <= INITIAL_START_UP_CURRENT[0]):
        test_output["initial_start_up"] = "PASS"
        return True
    test_output["initial_start_up"] = "FAIL"
    return False

def Input_Voltage_Sweep(DMM: Resource, PS: Resource, INITIAL_START_UP_VOLTAGE: list[float],
                        CALIBRATED_VOLTAGE_IN:float, test_output,
                        trace_output,debug:bool) -> bool:
    '''4.2.2 DCDC CONVERTER DOC'''

    #sets lower bound of calibrated voltage
    voltage = CALIBRATED_VOLTAGE_IN-0.1
    PS.write("VOLT " + str(voltage))
    time.sleep(0.5)
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.03')
    DMM.write('INIT')
    for i in range(200):
        PS.write("VOLT " + str(voltage))
        voltage += 0.2/200
        time.sleep(2/200)

    sample = []
    DMM.query("*OPC?")
    #get data read back from buffer
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples ", n)
    sample = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    datalist = list(sample.split(','))

    voltage = CALIBRATED_VOLTAGE_IN - 0.1
    PS.write("VOLT " + str(voltage))
    time.sleep(0.5)
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:OPEN (@3)")
    #stop on 3 start on 2
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.03')
    DMM.write('INIT')
    time.sleep(0.5)

    #hopefully this loop helps to regulate
    for i in range(200):
        PS.write("VOLT " + str(voltage))
        voltage += 0.2/200
        time.sleep(2/200)

    sample = []
    DMM.query("*OPC?")
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples ", n)
    sample = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    datalist2 = list(sample.split(','))

    #this block for out voltage, next for current read
    if debug:
        print(datalist)
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]),
              5) for i in range(len(datalist))]

    trace_output["input_voltage_sweep_voltage_trace"] = datalist
    datalist2 = [
        round(float(datalist2[i][:datalist2[i].index("E")]) * 10 ** int(datalist2[i][datalist2[i].index("E") + 1:]),
              5) for i in range(len(datalist2))]
    trace_output["input_voltage_sweep_current_trace"] = datalist2
    for i in range(100):
        mean_val = datalist[i]
        if mean_val <= INITIAL_START_UP_VOLTAGE[0] or mean_val >= INITIAL_START_UP_VOLTAGE[1]:
            test_output["input_voltage_sweep"] = "FAIL"
            return False

    test_output["input_voltage_sweep"] = "PASS"
    return True

def Nominal_Load_Performance(DMM: Resource, PS: Resource, RELAY,
                    VOLTAGE_RANGE: list[float], CALIBRATED_VOLTAGE_IN:float, test_output,
                             trace_output,debug:bool) -> bool:
    '''4.2.3 DCDC CONVERTER DOC'''
    #this will make semi-cont measurements and return based on final perf.
    DMM.write("*RST")
    #activates relay for 1 megaohn resistance channel
    #that is, channel 2
    RELAY.write(b"reset\r")
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")
    time.sleep(0.3)
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02') #/100 measurements in 2 sec
    DMM.write('INIT')
    time.sleep(0.5)

    RELAY.write(b"relay on\r") #this runs the relay for the 1 ohm resistor channel, if it times
    #out that may be an issue, but see if it works
    DMM.query("*OPC?")

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)
    RELAY.write(b"reset\r")

    DMM.write("ROUT:MULT:OPEN (@3)")
    #take back trace data, read all samples to a db eventually.
    PS.write("*RST")

    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        if debug:
            print(datalist)
        datalist = [
            round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
            for i in range(len(datalist))]
    else:
        #error but no throw for lack of entries
        test_output["nominal_load_performance"] = "ERR"
        return False
    time.sleep(0.5)

    #same thing but monitor current
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")
    DMM.write("*RST")
    time.sleep(0.3)
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02') #/100 measurements in 2 sec
    DMM.write('INIT')
    time.sleep(0.5)

    RELAY.write(b"relay on\r") #this runs the relay for the 1 ohm resistor channel, if it times
    #out that may be an issue, but see if it works
    DMM.query("*OPC?")

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)
    RELAY.write(b"reset\r")
    DMM.write("ROUT:MULT:OPEN (@2)")

    PS.write("*RST")
    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist2 = list(data.split(','))
        if debug:
            print(datalist2)
        datalist2 = [
            round(float(datalist2[i][:datalist2[i].index("E")]) * 10 **
                  int(datalist2[i][datalist2[i].index("E") + 1:]), 5)
            for i in range(len(datalist2))]
    else:
        # error but no throw for lack of entries
        test_output["nominal_load_performance"] = "ERR"
        return False

    #then save these outputs
    trace_output["nominal_load_voltage_trace"] = datalist
    trace_output["nominal_load_current_trace"] = datalist2

    if all([dp <= VOLTAGE_RANGE[1] and dp >=VOLTAGE_RANGE[0] for dp in datalist]):

        test_output["nominal_load_performance"] = "PASS"
        return True
    else:
        test_output["nominal_load_performance"] = "FAIL"
        return False

def Input_and_Ouput_Cold( DMM: Resource, PS: Resource,CALIBRATED_VOLTAGE_IN:float,
                          COLD_V,COLD_C,test_output,
                          trace_output,debug:bool) -> bool:
    '''4.3.2'''
    #essentially a copy of the warm version with lower params
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")

    PS.query("*OPC?")  # checks if the power supply is all correct
    sample_volts = []  # actual sa  mpling process on ch3, avg 10 samps in 1 sec
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

    test_result = round(np.mean(sample_volts), 3)
    test_result2 = round(np.mean(sample_mamps), 3)
    if debug:
        print("voltage debug results:")
        print(sample_volts)
        print(test_result)
        print("current debug results:")
        print(sample_mamps)
        print(test_result2)

    #append to df
    test_output["initial_cold_voltage"] = test_result
    test_output["initial_cold_current"] = test_result2
    if (test_result <= COLD_V[1] and test_result >= COLD_V[0]
            and test_result2 <= COLD_C[1] and test_result2 >= COLD_C[0]):
        test_output["input_current_output_voltage"] = "PASS"
        return True
    test_output["input_current_output_voltage"] = "FAIL"
    return False

def Input_Voltage_Step(DMM: Resource, PS: Resource, CALIBRATED_VOLTAGE_IN: float,
                       VOLTAGE_RANGE, test_output,
                       trace_output, debug:bool) ->bool:
    '''(4.3.4)'''

    DMM.write("*RST")
    PS.write("*RST")
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
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

    PS.write("VOLT " +str(CALIBRATED_VOLTAGE_IN +.1))

    #let me know when done, will throw all sorts of errors if something in the setup isnt perfect
    DMM.query('*OPC?')

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)

    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        if debug:
            print(datalist)
        #mangled scipi formatting, had to do it manually
        datalist = [round(float(datalist[i][:datalist[i].index("E")])*10**int(datalist[i][datalist[i].index("E")+1:]),5)
                    for i in range(len(datalist))]
    else:
        #errors on this test but does not break the testing loop
        test_output["input_step_voltage"] = "ERR"
        return False
    if debug:
        print("final debug voltage for step voltage test ", datalist[-1])

    #now we do the same thing but for current :/
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    DMM.write("*RST")
    time.sleep(1)
    DMM.write("ROUT:MULT:OPEN (@3)")
    PS.query("*OPC?")
    DMM.query("*OPC?")

    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02')
    DMM.write('INIT')
    time.sleep(0.5)

    #after the delay, bumps up again
    PS.write("VOLT " +str(CALIBRATED_VOLTAGE_IN +.1))

    DMM.query('*OPC?')

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)

    DMM.write("ROUT:MULT:OPEN (@2)")

    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist2 = list(data.split(','))
        if debug:
            print(datalist2)
        #mangled scipi formatting, had to do it manually
        datalist2 = [round(float(datalist2[i][:datalist2[i].index("E")])*10**
                           int(datalist2[i][datalist2[i].index("E")+1:]),5)
                    for i in range(len(datalist2))]

    #puts datalist as trace
    trace_output["input_step_voltage_voltage_trace"] =  datalist
    trace_output["input_step_voltage_current_trace"] = datalist2

    if all([dp <= VOLTAGE_RANGE[1] and dp >=VOLTAGE_RANGE[0] for dp in datalist]):
        #this is just seeign if none jump out of allowed range
        test_output["input_step_voltage"] = "PASS"
        return True

    test_output["input_step_voltage"] = "FAIL"
    return False

def Output_Step_Load(DMM: Resource, PS: Resource, RELAY, CALIBRATED_VOLTAGE_IN,
                     COLD_V,test_output, trace_output,debug:bool) ->bool:
    '''4.3.3'''
    DMM.write("*RST")
    RELAY.write(b"reset\r")
    DMM.write("ROUT:MULT:CLOS (@3)")
    PS.write("*RST")

    #activates channel relay for 1 mohm
    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    PS.write("OUTP ON")

    #this takes 100 measurements in 2 sec, just as above
    #if all fall within stable range within the time they are good.
    DMM.write('FUNC "VOLT:DC"')
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02')

    DMM.write('INIT')
    time.sleep(0.5)
    RELAY.write(b"relay on 000\r")

    #let me know when done
    DMM.query('*OPC?')
    #same traceback and rformatting as other testing blocks
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)
    RELAY.write(b"reset\r")

    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        if debug:
            print(datalist)
        # mangled scipi formatting, had to do it manually
        datalist = [
            round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
            for i in range(len(datalist))]
    else:
        test_output["output_step_load"] = "ERR" #error but do not throw if bad output
        return False
    if debug:
        print("final step voltage ", datalist[-1])

    #now we reset and do similar steps to get a current reading.
    DMM.write("*RST")
    time.sleep(0.5)
    DMM.write("ROUT:MULT:OPEN (@3)")
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.query("*OPC?")

    DMM.write('FUNC "VOLT:DC"')
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02')

    DMM.write('INIT')
    time.sleep(0.5)
    RELAY.write(b"relay on 000\r")

    #let me know when done
    DMM.query('*OPC?')
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples (current) :", n)
    if n > 0:
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist2 = list(data.split(','))
        if debug:
            print(datalist2)
        datalist2 = [
            round(float(datalist2[i][:datalist2[i].index("E")]) * 10 **
                  int(datalist2[i][datalist2[i].index("E") + 1:]), 5)
            for i in range(len(datalist2))]
        trace_output["output_step_load_current_trace"] = datalist2
        if debug:
            print("final step voltage (current) ", datalist2[-1])

    trace_output["output_step_load_voltage_trace"] = datalist

    if all([dp <=COLD_V[1] and dp >=COLD_V[0] for dp in datalist][-10:]):
        test_output["output_step_load"] = "PASS"
        return True
    else:
        test_output["output_step_load"] = "FAIL"
        return False

def Cold_Startup_Test(DMM: Resource, PS: Resource, CALIBRATED_VOLTAGE_IN, COLD_V,
                      test_output,trace_output,debug:bool,timer_debug: bool) -> bool:
    '''4.3.5'''
    #this test is just the warm start up but with cold specs
    PS.write("*RST")
    DMM.write("*RST")
    #have user manually do these steps
    input(Fore.MAGENTA + "Confirm that all power supply channels are OFF by pressing ENTER")
    input(Fore.MAGENTA + "Press ENTER to begin timer")
    print("Timer begun for 600 seconds...")
    #swithces off for full time to fully cool time
    Q_TIMER(600,timer_debug,snd)

    input(Fore.MAGENTA + "Timer end, press ENTER to continue")

    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    #start recording then activate ps
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.05')
    DMM.write('INIT')
    time.sleep(0.5)
    PS.write("OUTP ON")

    #oopsforgot to wait for actual recording so we only got 60 ms of trace data
    time.sleep(5)
    DMM.query('*OPC?')

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples ", n)
    if not n>0:
        #throw soft err if no data
        test_output["cold_startup"] = "ERR"
        return False
    #same proc for parsing data as other testing blocks
    data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    DMM.write("ROUT:MULT:OPEN (@3)")
    datalist = list(data.split(','))
    if debug:
        print(datalist)
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]),
              5) for i in range(len(datalist))]

    #saves data and trace
    trace_output["cold_startup_voltage_trace"] =  datalist

    #reset time lol
    PS.write("*RST")
    DMM.write("*RST")
    time.sleep(2)

    PS.write("INST CH1")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.050")
    # start recording then activate ps
    #this is basically a repeat of before but for current
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.05')
    DMM.write('INIT')
    time.sleep(0.5)
    PS.write("OUTP ON")

    time.sleep(5)
    # let me know when done
    DMM.query('*OPC?')

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples ", n)
    if not n > 0:
        test_output["cold_startup"] = "ERR"
        return False
    data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    DMM.write("ROUT:MULT:OPEN (@2)")
    datalist2 = list(data.split(','))
    if debug:
        print(datalist2)
    datalist2 = [
        round(float(datalist2[i][:datalist2[i].index("E")]) * 10 ** int(datalist2[i][datalist2[i].index("E") + 1:]),
              5) for i in range(len(datalist2))]

    # saves data and trace
    trace_output["cold_startup_current_trace"] = datalist2

    #this just tells us that it passes if it stabilizes by the ending 10 entries
    if all([dp <=COLD_V[1] and dp >=COLD_V[0] for dp in datalist][-10:]):
        test_output["cold_start_up"] = "PASS"
        return True
    test_output["cold_start_up"] = "FAIL"
    return False

def SINGLE_POWER_CYCLE_TEST(PS: Resource, DMM: Resource, which,
                            CALIBRATED_VOLTAGE_IN: bool, test_output, trace_output):
    '''Turns on board, waits for stabilization and then records continuously to 100 samples'''

    #initialization of PS and DMM
    pc_vols = []
    pc_cur = []
    DMM.write("*RST")
    DMM.write("*CLS")
    PS.write("*RST")
    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.033")

    #this is the same as multi cycle but just leaving the power on instead of looping
    time.sleep(0.1)
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.05')
    PS.write("OUTP ON")
    # this delay needed to be long as voltage is somewhat slow to stabilize from off state
    time.sleep(2)
    DMM.write('INIT')

    DMM.query("*OPC?")
    DMM.write("ROUT:MULT:OPEN (@3)")

    #saving and retrieving data
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    datalist = list(data.split(','))
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
        for i in range(len(datalist))]
    for i in datalist:
        pc_vols.append(i)

    #current measurement
    DMM.write('FUNC "VOLT:DC"')
    DMM.write("ROUT:MULT:CLOS (@2)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.05')
    time.sleep(0.3)
    DMM.write('INIT')

    DMM.query("*OPC?")
    DMM.write("ROUT:MULT:OPEN (@2)")

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    datalist = list(data.split(','))
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
        for i in range(len(datalist))]
    for i in datalist:
        pc_cur.append(i)

    PS.write("OUTP OFF")
    # Calculate statistics
    avg_voltage = round(np.mean(pc_vols), 5)
    std_voltage = round(np.std(pc_vols), 5)
    ave_current = round(np.mean(pc_cur), 5)

    # this selects which data sheet to update
    if which == "w":
        test_output["mc_ave_vol"] = avg_voltage
        test_output["mc_ave_cur"] = ave_current
        trace_output["multiple_power_cycle_voltage"] = pc_vols
        trace_output["multiple_power_cycle_current"] = pc_cur
        test_output["voltage_dev_warm"] = std_voltage
    elif which == "c":
        test_output["mc_ave_vol_c"] = avg_voltage
        test_output["mc_ave_cur_c"] = ave_current
        trace_output["multiple_power_cycle_voltage_c"] = pc_vols
        trace_output["multiple_power_cycle_current_c"] = pc_cur
        test_output["voltage_dev_cold"] = std_voltage

def POWER_CYCLE_TEST(PS,DMM,which,
                     CALIBRATED_VOLTAGE_IN: bool, test_output,trace_output):
    '''Turns on board, waits for stabilized time and then records, repeats 10 times.'''

    pc_vols = []
    pc_cur = []
    DMM.write("*RST")
    DMM.write("*CLS")
    PS.write("*RST")

    PS.write("VOLT " + str(CALIBRATED_VOLTAGE_IN))
    PS.write("CURR 0.033")
    for i in range(10):

    #i mostly just copied from aove to save times here
        time.sleep(0.1)
        DMM.write('FUNC "VOLT:DC"')
        DMM.write("ROUT:MULT:CLOS (@3)")
        DMM.write('TRAC:CLE "defbuffer1"')
        DMM.write('TRAC:POIN 10')
        DMM.write('TRIG:LOAD "SimpleLoop",10,0.05')
        PS.write("OUTP ON")
    # this delay needed to be long as voltage is somewhat slow to stabilize from off state
        time.sleep(2)
        DMM.write('INIT')

        DMM.query("*OPC?")
        DMM.write("ROUT:MULT:OPEN (@3)")

        n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        datalist = [
            round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
            for i in range(len(datalist))]
        for i in datalist:
            pc_vols.append(i)

        DMM.write('FUNC "VOLT:DC"')
        DMM.write("ROUT:MULT:CLOS (@2)")
        DMM.write('TRAC:CLE "defbuffer1"')
        DMM.write('TRAC:POIN 10')
        DMM.write('TRIG:LOAD "SimpleLoop",10,0.05')
        time.sleep(0.3)
        DMM.write('INIT')

        DMM.query("*OPC?")
        DMM.write("ROUT:MULT:OPEN (@2)")
        n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
        data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
        datalist = list(data.split(','))
        datalist = [
            round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]), 5)
            for i in range(len(datalist))]
        for i in datalist:
            pc_cur.append(i)

        PS.write("OUTP OFF")
        time.sleep(0.1)

    # Calculate statistics
    avg_voltage = np.mean(pc_vols)
    std_voltage = np.std(pc_vols)
    ave_current = np.mean(pc_cur)

    #this selects which data sheet to update
    if which == "w":
        test_output["mc_ave_vol"] = avg_voltage
        test_output["mc_ave_cur"] = ave_current
        trace_output["multiple_power_cycle_voltage"] = pc_vols
        trace_output["multiple_power_cycle_current"] = pc_cur
        test_output["voltage_dev_warm"] = std_voltage
    elif which == "c":
        test_output["mc_ave_vol_c"] = avg_voltage
        test_output["mc_ave_cur_c"] = ave_current
        trace_output["multiple_power_cycle_voltage_c"] =  pc_vols
        trace_output["multiple_power_cycle_current_c"] = pc_cur
        test_output["voltage_dev_cold"] = std_voltage