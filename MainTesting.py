from colorama import init, Fore, Back, Style

from Utilities import AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE

init(autoreset=True)
import Utilities
from WorkbookCreator import *
from Tests import *
print("booting...")

#init dbs if not already
init_db()

init_trace_db()
Utilities.DUNE_ASCII()

#====================================================TESTING PARAMS====================================================#
#These are to be chosen in accordance with the DC_DC Converter Report 2.1
#voltage autocalibration
IDEAL_INCOMING_VOLTAGE = 5.0
CALIBRATED_VOLTAGE_IN = 5.0
#4.2.1
INITIAL_START_UP_VOLTAGE = [58.0,61.0]
INITIAL_START_UP_CURRENT = [-0.035,-0.033]
#4.2.2
#4.3.5
OUTPUT_VOLTAGE_COLD = [48.0,50.0]
INPUT_CURRENT_COLD = [-0.025,-0.027]
#DEBUG CONFIG SETTINGS
SHORT_TEST_CYCLE = True     #abridges testing proc for early stage testing
OVERRIDE_RELAY = False      #uses multiple ps channels instead of relay to cycle loads
power_cycle_test = True     #turn this off during typical testing
debug = True #general debug to see more numbers during testing
#======================================================================================================================#

#Check for good multimeter and power supply connections
print("Checking for resources...")
RELAY = Utilities.SERIAL_CONNECTOR()
RM = pyvisa.ResourceManager()
DMM,PS = Utilities.RESOURCE_CONNECTOR(RM)

#if it makes it this far, we are good to go
print(Fore.GREEN + "All resources connected successfully.\n")

#Configure and reset meters
DMM.write("*RST")
DMM.write("*CLS")
DMM.write("SENS:FUNC 'VOLT:DC'")
PS.write("*RST")

#testing loop:
first = True
test_more_boards_o7 = True
while test_more_boards_o7:
#starts storing data for next board
    test_output = {
        "board_id": "NA", #warm
        "calibrated_voltage": -1,
        "initial_voltage": -1,
        "initial_current": -1,
        "initial_start_up": "NULL",
        "input_voltage_sweep": "NULL",
        "nominal_load_performance": "NULL",

        "mc_ave_vol": -1, #powercyles
        "mc_ave_cur": -1,

        "secondary_calibration":-1, #cold
        "initial_cold_voltage":-1,
        "initial_cold_current":-1,
        "input_current_output_voltage": "NULL",
        "output_step_load": "NULL",
        "input_step_voltage": "NULL",
        "cold_start_up": "NULL",
    }
    trace_output = {
        "input_voltage_sweep_voltage_trace": [],
        "input_voltage_sweep_current_trace": [],

        "nominal_load_voltage_trace": [],
        "nominal_load_current_trace": [],

        "multiple_power_cycle_voltage": [],
        "multiple_power_cycle_current": [],

        #this chord
        "input_step_voltage_voltage_trace": [],
        "input_step_voltage_current_trace": [],

        "output_step_load_voltage_trace": [],
        "output_step_load_current_trace": [],

        "cold_startup_voltage_trace": [],
        "cold_startup_current_trace": [],
    }

#reset power supply, ask user to replace board
    if not first:
        if input(Fore.MAGENTA + "Test Next Board? (y/n) ").lower() != "y":
            test_more_boards_o7 = False
            break
    PS.write("*RST")
    input(Fore.MAGENTA + "Confirm that all power supply channels are OFF by pressing ENTER")

    if first == True:
        first = False
    else:
        input(Fore.MAGENTA + "Replace current board with next, press ENTER to continue")

    #this chunk takes a board id and checks to see if db already has warm data, which we will skip if there
    test_output["board_id"] = input(Fore.MAGENTA + "Board ID: ")
    print()

    if SHORT_TEST_CYCLE:
        CALIBRATED_VOLTAGE_IN, inboard = Utilities.AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE(DMM, PS,
                                                                                       IDEAL_INCOMING_VOLTAGE,
                                                                                       CALIBRATED_VOLTAGE_IN, debug)
        POWER_CYCLE_TEST(PS,DMM,CALIBRATED_VOLTAGE_IN,test_output,trace_output)

    else:
        if not Utilities.WARM_TEST_EXISTS(str(test_output["board_id"])):

        #calibration of incoming voltage
            CALIBRATED_VOLTAGE_IN, inboard = Utilities.AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE(DMM, PS,
                                                IDEAL_INCOMING_VOLTAGE, CALIBRATED_VOLTAGE_IN,debug)
            test_output["calibrated_voltage"] = (str(round(CALIBRATED_VOLTAGE_IN,5)) +
                                                 " IN "+"/ "+str(round(inboard,5)) + " OUT")
        #4.2.1
            if Initial_Start_Up_Test(DMM, PS, INITIAL_START_UP_VOLTAGE,INITIAL_START_UP_CURRENT,
                                     CALIBRATED_VOLTAGE_IN, test_output,trace_output,debug):
                print("INITIAL START UP: ", Fore.GREEN + "PASS")
            else:
                print("INITIAL START UP: ", Fore.RED + "FAIL")
        #4.2.2
            time.sleep(0.5)
            if Input_Voltage_Sweep(DMM, PS, INITIAL_START_UP_VOLTAGE,
                                   CALIBRATED_VOLTAGE_IN, test_output,trace_output,debug):
                print("INPUT VOLTAGE SWEEP: ", Fore.GREEN + "PASS")
            else:
                print("INPUT VOLTAGE SWEEP: ", Fore.RED + "FAIL")
        #4.2.3
            time.sleep(0.5)
            if Nominal_Load_Performance(DMM, PS, RELAY,OVERRIDE_RELAY, INITIAL_START_UP_VOLTAGE, CALIBRATED_VOLTAGE_IN,
                                        test_output,trace_output,debug):
                print("NOMINAL LOAD STABILIZATION: ", Fore.GREEN + "PASS")
            else:
                print("NOMINAL LOAD STABILIZATION: ", Fore.RED + "FAIL")

        #save trace data for warm testing
        insert_warm_traces(test_output["board_id"],
                           trace_output["input_voltage_sweep_trace"], trace_output["nominal_load_trace"])
        insert_test(test_output)
        #that should be it for the warm loop, then ask user if continue to cold testing

        if input(Fore.MAGENTA + "Continue to Cold Testing? (y/n) ").lower() == "y":
            #not entirely needed, but reset just to be safe
            #this should keep the power at an expected level during quenching
            PS.write("*RST")
            DMM.write("*RST")
            PS.write("INST CH1")
            PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
            PS.write("CURR 0.05")
            PS.write("OUTP ON")
            input(Fore.MAGENTA + "Submerge board in liquid argon for 300 seconds, press ENTER to start timer")
            print("Timer begun for 300 seconds...")
            if debug:
                time.sleep(3)
            else:
                time.sleep(3)
            input(Fore.MAGENTA +"Timer end, press ENTER to continue")
        else:
            print(Fore.LIGHTCYAN_EX + "PARTIAL TEST RESULTS EXPORTED")
            continue

    #secondary calibration for cold testing

        PS.write("*RST")
        CALIBRATED_VOLTAGE_IN, inboard = Utilities.AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE(DMM, PS,
                                            IDEAL_INCOMING_VOLTAGE, CALIBRATED_VOLTAGE_IN,debug)
        test_output["secondary_calibration"] = (str(round(CALIBRATED_VOLTAGE_IN,5)) +
                                             " IN "+"/ "+str(round(inboard,5)) + " OUT")
    #4.3.2
        if Input_and_Ouput_Cold(DMM,PS,CALIBRATED_VOLTAGE_IN,
                                OUTPUT_VOLTAGE_COLD,INPUT_CURRENT_COLD,test_output,trace_output,debug):
            print("INITIAL COLD INPUT/OUTPUT: ", Fore.GREEN + "PASS")

        else:
            print("INITIAL COLD INPUT/OUTPUT: ", Fore.RED + "FAIL")
        time.sleep(0.5)
    #4.3.3
        if  Output_Step_Load(DMM,PS, RELAY, OVERRIDE_RELAY, CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD
                ,test_output,trace_output,debug):
            print("OUTPUT STEP VOLTAGE: "+ Fore.GREEN + "PASS")
        else:
            print("OUTPUT STEP VOLTAGE: "+ Fore.RED + "FAIL")
        time.sleep(0.5)
    #4.3.4
        if Input_Voltage_Step(DMM,PS,CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD,test_output,trace_output,debug):
            print("INPUT VOLTAGE STEP: ", Fore.GREEN + "PASS")
        else:
            print("INPUT VOLTAGE STEP: ", Fore.RED + "FAIL")
    #4.3.6
        time.sleep(0.5)
        if Cold_Startup_Test(DMM,PS,CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD,test_output,trace_output,debug):
            print("INPUT VOLTAGE STEP: ", Fore.GREEN + "PASS")
        else:
            print("INPUT VOLTAGE STEP: ", Fore.RED + "FAIL")

    #log final results for this board
        update_cold_test(test_output)
        update_cold_traces(trace_output)
        print(Fore.LIGHTCYAN_EX + "TEST RESULTS EXPORTED")
        DMM.write("*CLS")

#safely close resources i hope
PS.write("*RST")
DMM.write("*RST")
RM.close()
