import sys
import time
import pyvisa
from colorama import init, Fore, Back, Style
from winsound import MB_ICONASTERISK
import Utilities
from Utilities import RESOURCE_CONNECTOR
from WorkbookCreator import *
from Tests import *
init(autoreset=True)

#init dbs if not already
init_db()
init_nstab_db()
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
#4.3.2
OUTPUT_VOLTAGE_COLD = [48.0,50.0]#ask mike hwy this is a tigheter range
INPUT_CURRENT_COLD = [-0.025,-0.027]
#======================================================================================================================#

#Check for good multimeter and power supply connections
RM = pyvisa.ResourceManager()
DMM,PS = RESOURCE_CONNECTOR(RM)

#if it makes it this far, we are good to go
print(Fore.GREEN + "All resources connected successfully.\n")

#Configure and reset meters
DMM.write("*RST")
DMM.write("*CLS")
DMM.write("SENS:FUNC 'VOLT:DC'")
PS.write("*RST")

#testing loop:
test_output = {}
test_more_boards_o7 = True
while test_more_boards_o7:
#starts storing data for next board
    test_output = {
        "board_id": "NA",
        "calibrated_voltage": -1,
        "initial_voltage": -1,
        "initial_current": -1,
        "initial_start_up": "NULL",
        "input_voltage_sweep": "NULL",
        "nominal_load_performance": "NULL",
        "output_emi": "NULL",
        "secondary_calibration":-1,
        "initial_cold_voltage":-1,
        "initial_cold_current":-1,
        "input_current_output_voltage": "NULL",
        "output_step_load": "NULL",
        "input_step_voltage": "NULL",
        "output_noise_voltage": "NULL",
        "cold_start_up": "NULL",
    }
    nstab_test_output = {
        "board_id": "NA",
        "n0":-1,
        "n1":-1,
        "n2":-1,
        "n3":-1,
        "n4":-1,
        "n5": -1,
        "n6": -1,
        "n7": -1,
        "n8": -1,
        "n9": -1
    }

#reset power supply, ask user to replace board
    if input(Fore.MAGENTA + "Test Next Board? (y/n) ").lower() != "y":
        test_more_boards_o7 = False
        break
    PS.write("*RST")
    input(Fore.MAGENTA + "Confirm that all power supply channels are OFF by pressing ENTER")
    input(Fore.MAGENTA + "Replace current board with next, press ENTER to continue")
    test_output["board_id"] = input(Fore.MAGENTA + "Board ID: ")

#calibration of incoming voltage
    CALIBRATED_VOLTAGE_IN, inboard = Calibrate_to_Ideal_Incoming_Voltage(DMM, PS,
                                        IDEAL_INCOMING_VOLTAGE, CALIBRATED_VOLTAGE_IN)
    test_output["calibrated_voltage"] = (str(round(CALIBRATED_VOLTAGE_IN,5)) +
                                         " IN "+"/ "+str(round(inboard,5)) + " OUT")
#4.2.1
    if Initial_Start_Up_Test(DMM, PS, INITIAL_START_UP_VOLTAGE,INITIAL_START_UP_CURRENT,
                             CALIBRATED_VOLTAGE_IN, test_output):
        print("INITIAL START UP: ", Fore.GREEN + "PASS")
    else:
        print("INITIAL START UP: ", Fore.RED + "FAIL")
#4.2.2
    time.sleep(0.5)
    if Input_Voltage_Sweep(DMM, PS, INITIAL_START_UP_VOLTAGE, CALIBRATED_VOLTAGE_IN, test_output):
        print("INPUT VOLTAGE SWEEP: ", Fore.GREEN + "PASS")
    else:
        print("INPUT VOLTAGE SWEEP: ", Fore.RED + "FAIL")
#4.2.3
    time.sleep(0.5)
    if Nominal_Load_Performance(DMM, PS, INITIAL_START_UP_VOLTAGE, CALIBRATED_VOLTAGE_IN, test_output,nstab_test_output):
        print("NOMINAL LOAD STABILIZATION: ", Fore.GREEN + "PASS")
    else:
        print("NOMINAL LOAD STABILIZATION: ", Fore.RED + "FAIL")

    if input(Fore.MAGENTA + "Continue to Cold Testing? (y/n) ").lower() == "y":
        #not entirely needed, but reset just to be safe
        #what does leaving power on here look like
        PS.write("*RST")
        DMM.write("*RST")
        print("Timer begun for 300 seconds...")
        time.sleep(3)
        input(Fore.MAGENTA +"Timer end, press ENTER to continue")
    else:
        continue

#secondary calibration for cold testing

    CALIBRATED_VOLTAGE_IN, inboard = Calibrate_to_Ideal_Incoming_Voltage(DMM, PS,
                                        IDEAL_INCOMING_VOLTAGE, CALIBRATED_VOLTAGE_IN)
    test_output["secondary_calibration"] = (str(round(CALIBRATED_VOLTAGE_IN,5)) +
                                         " IN "+"/ "+str(round(inboard,5)) + " OUT")
#4.3.2
    if Input_and_Ouput_Cold(DMM,PS,CALIBRATED_VOLTAGE_IN,
                            OUTPUT_VOLTAGE_COLD,INPUT_CURRENT_COLD,test_output):
        print("INITIAL COLD INPUT/OUTPUT: ", Fore.GREEN + "PASS")
    else:
        print("INITIAL COLD INPUT/OUTPUT: ", Fore.RED + "FAIL")
#4.3.4
    if Input_Voltage_Step(DMM,PS,CALIBRATED_VOLTAGE_IN,INITIAL_START_UP_VOLTAGE,test_output):
        print("INPUT VOLTAGE STEP: ", Fore.GREEN + "PASS")
    else:
        print("INPUT VOLTAGE STEP: ", Fore.RED + "FAIL")

#log final results for this board
    insert_test(test_output)
    print(Fore.LIGHTCYAN_EX + "TEST RESULT EXPORTED")

#safely close resources i hope
PS.write("*RST")
DMM.write("*RST")
RM.close()

if input(Fore.MAGENTA + "Download DATA as .XLSX? (y/n) ") == 'y':
    export_to_excel()
    time.sleep(0.5)
    print(Fore.LIGHTCYAN_EX + "DOWNLOAD COMPLETE")
