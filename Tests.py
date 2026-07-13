import time
import pyvisa
from colorama import init, Fore, Back, Style
init(autoreset=True)
import numpy as np
from pyvisa import Resource
import matplotlib.pyplot as mp
show_plots = False

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
                        CALIBRATED_VOLTAGE_IN:float, test_output,
                        trace_output,debug:bool) -> bool:
    '''4.2.2 DCDC CONVERTER DOC'''

    #sets lower bound of calibrated voltage
    #!!!this test has a total trace time of 3000 ms to allow for PS write time
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
    if debug:
        print(datalist)
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]),
              5) for i in range(len(datalist))]

    trace_output["input_voltage_sweep_trace"] = datalist
    for i in range(100):
        mean_val = datalist[i]
        if mean_val <= INITIAL_START_UP_VOLTAGE[0] or mean_val >= INITIAL_START_UP_VOLTAGE[1]:
            test_output["input_voltage_sweep"] = "FAIL"
            return False

    test_output["input_voltage_sweep"] = "PASS"
    return True

def Nominal_Load_Performance(DMM: Resource, PS: Resource, VOLTAGE_RANGE: list[float],
                        CALIBRATED_VOLTAGE_IN:float, test_output, trace_output,debug:bool) -> bool:
    '''4.2.3 DCDC CONVERTER DOC'''
    #this will make semi-cont measurements and return based on final perf.
    DMM.write("*RST")
    #activates relay for 1 megaohn resistance channel
    #that is, channel 2
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
    PS.write("INST CH2")
    PS.write("VOLT 5")
    PS.write("CURR 0.200")
    PS.write("OUTP ON")
    DMM.query("*OPC?")

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)

    #take back trace data, read all samples to a db eventually.
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
        test_output["input_voltage_sweep"] = "ERR"
        return False

    trace_output["nominal_load_trace"] = datalist
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
    '''4.3.4'''

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
        if show_plots:
            mp.plot(datalist)
            mp.xlabel("Time (ms)")
            mp.ylabel("Voltage (V)")
            mp.show()
    else:
        #errors on this test but does not break the testing loop
        test_output["input_step_voltage"] = "ERR"
        return False
    if debug:
        print("final debug voltage for step voltage test ", datalist[-1])

    #puts datalist as trace
    trace_output["input_step_voltage_trace"] = datalist
    if all([dp <= VOLTAGE_RANGE[1] and dp >=VOLTAGE_RANGE[0] for dp in datalist]):
        #this is just seeign if none jump out of allowed range
        test_output["input_step_voltage"] = "PASS"
        return True

    test_output["input_step_voltage"] = "FAIL"
    return False

def Output_Step_Load(DMM: Resource, PS: Resource, CALIBRATED_VOLTAGE_IN, COLD_V,
                     test_output, trace_output,debug:bool) ->bool:
    '''4.3.3'''
    DMM.write("*RST")
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
    DMM.write("ROUT:MULT:CLOS (@3)")
    DMM.write('TRAC:CLE "defbuffer1"')
    DMM.write('TRAC:POIN 100')
    DMM.write('TRIG:LOAD "SimpleLoop",100,0.02')

    DMM.write('INIT')
    time.sleep(0.5)

    PS.write("INST CH2")
    PS.write("VOLT 5")  #again, this is fine to be any voltage around 5 as long as it opens the relay
    PS.write("CURR 0.200")
    PS.write("OUTP ON")
    PS.query("*OPC?")

    #let me know when done
    DMM.query('*OPC?')
    #same traceback and rformatting as other testing blocks
    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples:", n)

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
        test_output["output_step_voltage"] = "ERR" #error but do not throw if bad output
        return False
    if debug:
        print("final step voltage ", datalist[-1])

    trace_output["output_step_load_trace"] = datalist
    if all([dp <=COLD_V[1] and dp >=COLD_V[0] for dp in datalist]):
        test_output["output_step_voltage"] = "PASS"
        return True
    else:
        test_output["output_step_voltage"] = "FAIL"
        return False

def Cold_Startup_Test(DMM: Resource, PS: Resource, CALIBRATED_VOLTAGE_IN, COLD_V,
                      test_output,trace_output,debug:bool) -> bool:
    '''4.3.5'''
    #this test is just the warm start up but with cold specs
    PS.write("*RST")
    DMM.write("*RST")
    #have user manually do these steps
    input(Fore.MAGENTA + "Confirm that all power supply channels are OFF by pressing ENTER")
    input(Fore.MAGENTA + "Disconnect DC_DC Board from test stand and submerge in liguid argon, "
                         "press ENTER to continue")
    print("Timer begun for 600 seconds...")
    time.sleep(600)
    input(Fore.MAGENTA + "Timer end, reconnect board and press ENTER to continue")

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

    n = int(DMM.query('TRAC:ACT? "defbuffer1"'))
    if debug:
        print("samples ", n)
    if not n>0:
        #throw soft err if no data
        test_output["cold_startup"] = "ERR"
        return False
    #same proc for parsing data as other testing blocks
    data = DMM.query(f'TRAC:DATA? 1,{n},"defbuffer1",READ')
    datalist = list(data.split(','))
    if debug:
        print(datalist)
    datalist = [
        round(float(datalist[i][:datalist[i].index("E")]) * 10 ** int(datalist[i][datalist[i].index("E") + 1:]),
              5) for i in range(len(datalist))]

    if show_plots:
        mp.plot(datalist)
        mp.xlabel("Time (ms)")
        mp.ylabel("Voltage (V)")
        mp.title("Cold Startup Test")
        mp.show()

    #saves data and trace
    trace_output["cold_startup_trace"] = datalist
    print(datalist)
    if all([dp <=COLD_V[1] and dp >=COLD_V[0] for dp in datalist]):
        test_output["cold_startup"] = "PASS"
        return True
    test_output["cold_startup"] = "FAIL"
    return False