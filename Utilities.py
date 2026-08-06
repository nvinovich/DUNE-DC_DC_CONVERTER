import sys
import time
import winsound
import sqlite3
import serial
from serial.tools import list_ports
from colorama import init, Fore, Back, Style
init(autoreset=True)
import pyvisa
from pyvisa import Resource
from WorkbookCreator import get_connection
#this is a set of quality of life and connection utilities which would mainly be clutter in the other files

def DUNE_ASCII():
    print(Fore.MAGENTA +" ▄▄▄▄▄▄   ▄▄▄  ▄▄▄ ▄▄▄    ▄▄▄  ▄▄▄▄▄▄▄\n",
    Fore.MAGENTA +"███▀▀██▄ ███  ███ ████▄  ███ ███▀▀▀▀▀\n",
    Fore.MAGENTA +"███  ███ ███  ███ ███▀██▄███ ███▄▄\n",
    Fore.MAGENTA +"███  ███ ███▄▄███ ███  ▀████ ███\n",
    Fore.MAGENTA +"██████▀  ▀██████▀ ███    ███ ▀███████\n",
    Fore.MAGENTA +"DEEP UNDERGROUND NEUTRINO EXPERIMENT")

def Q_TIMER(t,t_debug,snd):
    '''timer, a very silly one at that. makes a little beep when done'''
    if t_debug:
        time.sleep(t/100)
    else:
        for i in range(int(t/100)):
            print(str(t-i*t) + " seconds remaining...")
            time.sleep(100)
    if snd:
        winsound.Beep(560, 1200)
        time.sleep(0.5)
        winsound.Beep(560, 1200)

def RESOURCE_CONNECTOR(RM)->(Resource,Resource):
    '''CONNECTS DMM THEN PS'''
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
                print(Fore.MAGENTA+"DMM connected:", manufacturer+", "+model+" "+serial)

            elif model == "E36312A":
                PS = device
                print(Fore.MAGENTA+"PS connected:", manufacturer+", "+model+" "+serial)
        except Exception:
            continue

    if DMM is None:
        RM.close()
        sys.exit("No digital multimeter found.")
    if PS is None:
        RM.close()
        sys.exit("No power supply found.")

    return DMM, PS

def WARM_TEST_EXISTS(board_id: str,phase: str) ->bool:
    #helps to skip warm testing if already done
    #had to update for new db formatting as well
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    initial_start_up,
                    input_voltage_sweep,
                    nominal_load_performance
                FROM dc_dc_tests
                WHERE board_id = %s
                AND phase = %s
                ORDER BY id DESC
                LIMIT 1
            """, (board_id,phase,))

            row = cursor.fetchone()

    if row is None:
        # Board does not exist yet
        return False

    # All three warm tests completed
    return all(value not in (None, "NULL") for value in row)

def SERIAL_CONNECTOR(baudrate=19200,timeout=1):
    '''Checks all COM channels for serial connection to relay board'''
    RELAY = None
    rport = None
    ports = list_ports.comports()
    #this might be overkill but check all ports until we find a valid connection
    for port in ports:
        if "Numato" in port.description:
            try:
                time.sleep(1) #allows for init time on device
                RELAY = serial.Serial(port.device, baudrate, timeout=timeout)
                rport = port
                break
            except serial.SerialException:
                pass
        if "USB Serial" in port.description:
            try:
                time.sleep(1)
                RELAY = serial.Serial(port.device, baudrate, timeout=timeout)
                rport = port
                break
            except serial.SerialException:
                pass

    #if no valid connection, throw
    if RELAY != None:
        print(Fore.MAGENTA + "RELAY connected: ", rport.description)
        RELAY.write(b"relay off 0\r")
        RELAY.write(b"relay off 1\r")
        RELAY.write(b"relay off 2\r")
        RELAY.write(b"relay off 3\r")
        time.sleep(0.2)
        RELAY.reset_input_buffer()
        return RELAY
    sys.exit("No serial relay connection found.")

def AUTOCALIBRATE_TO_IDEAL_INCOMING_VOLTAGE(  DMM: Resource, PS: Resource, IDEAL_INCOMING_VOLTAGE: float,
                                        CALIBRATED_VOLTAGE_IN: float,debug:bool) -> (float,float):
    '''Makes minimal adjustments to get incoming voltage to 5 volts with up to 0.01 VOLT error'''
    #reset calibrated voltage
    CALIBRATED_VOLTAGE_IN = 5.0
    PS.write("*RST")
    DMM.write("*RST")
    PS.write("*CLS")
    time.sleep(0.3)
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
            sys.exit("AUTOCALIBRATION FAILED DUE TO TIMEOUT AT " + str(final_time) + " SEC.")
        if debug:
            print(CALIBRATED_VOLTAGE_IN)
            print("error of " + str(abs(incoming_volts - IDEAL_INCOMING_VOLTAGE)))

        if (incoming_volts - IDEAL_INCOMING_VOLTAGE) >= tolerance:
            #if error >=
            CALIBRATED_VOLTAGE_IN -=0.0025*IDEAL_INCOMING_VOLTAGE
        if (incoming_volts - IDEAL_INCOMING_VOLTAGE) <= -tolerance:
            CALIBRATED_VOLTAGE_IN +=0.0025*IDEAL_INCOMING_VOLTAGE
        PS.write("VOLT "+str(CALIBRATED_VOLTAGE_IN))
        PS.query("*OPC?")
        time.sleep(0.05)

        incoming_volts = float(DMM.query("READ?"))
        time.sleep(0.5)
        Calibration_Timeout -=1

        if CALIBRATED_VOLTAGE_IN >= 5.5:
            #throws a fun new error for severe over or under voltage, prompt a hardware check
            DMM.write("*RST")
            PS.write("*RST")
            final_time = round(time.time() - start_time, 3)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            sys.exit("AUTOCALIBRATION FAILED DUE TO EXCESS OVER VOLTAGE AT " + str(final_time) + " SEC.")
        if CALIBRATED_VOLTAGE_IN <= 4.5:
            DMM.write("*RST")
            PS.write("*RST")
            final_time = round(time.time() - start_time, 3)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            sys.exit("AUTOCALIBRATION FAILED DUE TO EXCESS UNDER VOLTAGE AT " + str(final_time) + " SEC.")

    if debug:
        final_time = round(time.time() - start_time,3)
        print(Back.LIGHTCYAN_EX + Fore.BLACK + str(final_time) + " sec. elapsed in calibration")
    else:
        print("INPUT VOLTAGE CALIBRATED TO " + Fore.GREEN + str(round(CALIBRATED_VOLTAGE_IN,5)), "VOLTS, OUTPUT OF "
              + Fore.GREEN+str(round((incoming_volts),5)), "VOLTS")
    DMM.write("*RST")

    return CALIBRATED_VOLTAGE_IN, incoming_volts

def convert_scientific_to_float(value):
    '''just a stupid little utility to convert types when needed in parsing'''
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value

    return value

def SELECT_PHASE():
    """
    Displays all allowed testing phases and returns the one selected by the user.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT phase
                FROM test_phases
                ORDER BY phase
            """)

            phases = [row[0] for row in cursor.fetchall()]

    if not phases:
        raise ValueError("No testing phases found.")
    print(Fore.MAGENTA + "\nAvailable Testing Phases")

    for i, phase in enumerate(phases, start=1):
        print(f"{i}) {phase}")

    while True:
        try:
            choice = int(input(Fore.MAGENTA + "Select phase (by number): "))

            if 1 <= choice <= len(phases):
                return phases[choice - 1]

            print("Invalid selection.")

        except ValueError:
            print("Enter a number.")