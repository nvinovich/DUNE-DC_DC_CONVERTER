import winsound
from colorama import init, Fore, Back, Style
from psycopg.errors import UniqueViolation

from Utilities import Q_TIMER

init(autoreset=True)
import Utilities
from WorkbookCreator import *
from Tests import *
from tkinter import *
from tkinter import ttk
from Config import *

Utilities.DUNE_ASCII()

if __name__=='__main__':

    #Check for good multimeter and power supply connections
    print(Fore.CYAN + "COMPREHENSIVE DCDC CONVERTER TESTING CYCLE")

    # init dbs if not already
    print("Connecting to database...")
    init_db()
    init_phase_table()
    init_trace_db()

    print("Checking for resources...")
    RELAY = Utilities.SERIAL_CONNECTOR()
    RM = pyvisa.ResourceManager()
    DMM,PS = Utilities.RESOURCE_CONNECTOR(RM)

    #if it makes it this far, we are good to go
    print(Fore.GREEN + "All resources connected successfully.")

    #Configure and reset meters
    DMM.write("*RST")
    DMM.write("*CLS")
    DMM.write("SENS:FUNC 'VOLT:DC'")
    PS.write("*RST")
    DMM.write("ROUT:MULT:OPEN (@3)")
    DMM.write("ROUT:MULT:OPEN (@2)")
    DMM.write("ROUT:MULT:OPEN (@1)")

    #testing loop:
    first = True
    test_more_boards_o7 = True

    #ask for phase and admin name
    phase = Utilities.SELECT_PHASE()
    admin = input(Fore.MAGENTA + "Tests administered by: " )
    print()

    while test_more_boards_o7:
    #starts storing data for next board
        test_output = {
            "board_id": "NA", #warm
            "phase": phase,
            "testing_admin": admin,

            "calibrated_voltage": -1,
            "initial_voltage": -1,
            "initial_current": -1,
            "initial_start_up": "NULL",
            "input_voltage_sweep": "NULL",
            "nominal_load_performance": "NULL",

            "mc_ave_vol": -1, #powercyles
            "voltage_dev_warm":-1,
            "mc_ave_cur": -1,

            "mc_ave_vol_c": -1, #powercylescold
            "voltage_dev_cold":-1,
            "mc_ave_cur_c": -1,

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

            "multiple_power_cycle_voltage_c": [],
            "multiple_power_cycle_current_c": [],
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
            input(Fore.MAGENTA + "Replace current board if needed, press ENTER to continue")

        #this chunk takes a board id and checks to see if db already has warm data, which we will skip if there
        test_output["board_id"] = input(Fore.MAGENTA + "Board ID: ")

        # cold or warm
        CorW = input(Fore.MAGENTA + "Warm or Cold Testing? (W/c) ").lower()

        if CorW == 'w':
            input(Fore.MAGENTA + "Press ENTER to continue")
            print()

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
            if Nominal_Load_Performance(DMM, PS, RELAY, INITIAL_START_UP_VOLTAGE, CALIBRATED_VOLTAGE_IN,
                                        test_output,trace_output,debug):
                print("NOMINAL LOAD STABILIZATION: ", Fore.GREEN + "PASS")
            else:
                print("NOMINAL LOAD STABILIZATION: ", Fore.RED + "FAIL")

            if power_cycle_test and not cold_only:

                #option to do power cycle testing, does take an extra ~30 sec per board

                SINGLE_POWER_CYCLE_TEST(PS, DMM, CorW, CALIBRATED_VOLTAGE_IN, test_output, trace_output)

                test_output["calibrated_voltage_warm"] = (str(round(CALIBRATED_VOLTAGE_IN, 5)) +
                                                          " IN " + "/ " + str(round(inboard, 5)) + " OUT")
                if all([test_output["mc_ave_vol"] <= INITIAL_START_UP_VOLTAGE[1], test_output["mc_ave_vol"] >=
                                                                                  INITIAL_START_UP_VOLTAGE[0]]):
                    # pass condition ^
                    test_output["within_range1"] = "PASS"
                    print("WARM OPERATIONAL RANGE: ", Fore.GREEN + "PASS")
                else:
                    test_output["within_range1"] = "FAIL"
                    print("WARM OPERATIONAL RANGE: ", Fore.RED + "FAIL")

        #save data for warm testing
            insert_warm_traces(test_output["board_id"],test_output["phase"],
                           trace_output)
            try:
                insert_test(test_output)
            except UniqueViolation:
                print("This board has already been tested in this phase.")
            print(Fore.LIGHTCYAN_EX + "WARM TEST RESULTS EXPORTED")

        elif CorW == 'c':        #cold
            if not Utilities.WARM_TEST_EXISTS(str(test_output["board_id"]),str(test_output["phase"])):
                #doesnt let you write ahead without the warm tests for benchmark
                print(Fore.RED + f"No warm tests exist for{test_output['board_id']}")
                continue

            #this should keep the power at an expected level during quenching
            PS.write("*RST")
            DMM.write("*RST")
            PS.write("INST CH1")
            PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
            PS.write("CURR 0.05")
            PS.write("OUTP ON")
            input(Fore.MAGENTA + "Submerge board in liquid argon for 300 seconds, press ENTER to start timer")
            #timing function
            Q_TIMER(300,timer_debug,snd)

            input(Fore.MAGENTA +"Timer end, press ENTER to continue")

        #secondary calibration for cold testing
            CALIBRATED_VOLTAGE_IN, inboard = Utilities.AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE(DMM, PS,
                                                                                               IDEAL_INCOMING_VOLTAGE,
                                                                                               CALIBRATED_VOLTAGE_IN,
                                                                                               debug)
            test_output["secondary_calibration"] = (str(round(CALIBRATED_VOLTAGE_IN, 5)) +
                                                    " IN " + "/ " + str(round(inboard, 5)) + " OUT")
            #changed power cycle testing to be earlier to allow for stabilization.
            if power_cycle_test:

                SINGLE_POWER_CYCLE_TEST(PS, DMM, CorW,CALIBRATED_VOLTAGE_IN , test_output, trace_output)

                if all([test_output["mc_ave_vol_c"] <= OUTPUT_VOLTAGE_COLD[1], test_output["mc_ave_vol_c"] >=
                                                                               OUTPUT_VOLTAGE_COLD[0]]):
                    # pass condition ^
                    test_output["within_range2"] = "PASS"
                    print("COLD OPERATIONAL RANGE: ", Fore.GREEN + "PASS")
                else:
                    test_output["within_range2"] = "FAIL"
                    print("COLD OPERATIONAL RANGE: ", Fore.RED + "FAIL")

            PS.write("*RST")
        #4.3.2
            if Input_and_Ouput_Cold(DMM,PS,CALIBRATED_VOLTAGE_IN,
                                    OUTPUT_VOLTAGE_COLD,INPUT_CURRENT_COLD,test_output,trace_output,debug):
                print("INITIAL COLD INPUT/OUTPUT: ", Fore.GREEN + "PASS")

            else:
                print("INITIAL COLD INPUT/OUTPUT: ", Fore.RED + "FAIL")
            time.sleep(0.5)
        #4.3.3
            if  Output_Step_Load(DMM,PS, RELAY, CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD
                    ,test_output,trace_output,debug):
                print("NOMINAL LOAD COLD: "+ Fore.GREEN + "PASS")
            else:
                print("NOMINAL LOAD COLD: "+ Fore.RED + "FAIL")
            time.sleep(0.5)
        #4.3.4
            if Input_Voltage_Step(DMM,PS,CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD,test_output,trace_output,debug):
                print("INPUT VOLTAGE STEP: ", Fore.GREEN + "PASS")
            else:
                print("INPUT VOLTAGE STEP: ", Fore.RED + "FAIL")

            time.sleep(0.5)

        # 4.3.6
            if Cold_Startup_Test(DMM,PS,CALIBRATED_VOLTAGE_IN,OUTPUT_VOLTAGE_COLD,test_output,trace_output,
                                 debug,timer_debug):
                print("COLD START UP: ", Fore.GREEN + "PASS")
            else:
                print("COLD START UP: ", Fore.RED + "FAIL")

        #log final results for this board
            update_cold_test(test_output)
            update_cold_traces(test_output["board_id"],test_output["phase"], trace_output)
            print(Fore.LIGHTCYAN_EX + "COLD TEST RESULTS EXPORTED")
            DMM.write("*CLS")

        else:
            print(Fore.RED + "Invalid Input")
            continue

        if debug:
            print(test_output)
            print(trace_output)

        print()

    #safely close resources
    PS.write("*RST")
    DMM.write("*RST")
    RM.close()
