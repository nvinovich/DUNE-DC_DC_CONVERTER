import sys
import time
import pyvisa
from colorama import init, Fore, Back, Style
from Tests import *
init(autoreset=True)

#====================================================TESTING PARAMS====================================================#
#These are to be chosen in accordance with the DC_DC Converter Report 2.1
INITIAL_START_UP_VOLTAGE = 5
INITIAL_START_UP_CURRENT = 0
#Input Voltage Sweep
VOLTAGE_SWEEP_RNG = [4.9,5.1]
#======================================================================================================================#

#Check for good multimeter and power supply connections
print("Checking for resources...")
RM = pyvisa.ResourceManager()
resources = RM.list_resources()

if len(resources) == 0:
    sys.exit("No resources found.")

DMM = None
PS = None

for r in resources:
    try:
        device = RM.open_resource(r)
        idn = device.query("*IDN?").strip()

        manufacturer, model, serial, firmware = idn.split(",")

        #check for dmm, these are hardcoded as specific models for now
        if model == "MODEL DMM6500":
            DMM = device
            print(Fore.MAGENTA + "DMM connected:", idn)

        #check for power supply
        elif model == "E36312A":
            PS = device
            print(Fore.MAGENTA+ "PS connected:", idn)

    except Exception:
        continue

if DMM is None:
    sys.exit("No digital multimeter found.")
if PS is None:
    sys.exit("No power supply found.")

#if it makes it this far, we are good to go
print(Fore.GREEN + "All resources connected successfully.\n")

#Configure and reset meters
DMM.write("*RST")
DMM.write("*CLS")
DMM.write("SENS:FUNC 'VOLT:DC'")
PS.write("*RST")

if Initial_Start_Up_Test(DMM, PS, INITIAL_START_UP_VOLTAGE,INITIAL_START_UP_CURRENT):
    print("INITIAL START UP: ", Fore.GREEN + "PASS")
else:
    print("INITIAL START UP: ", Fore.RED + "FAIL")

time.sleep(0.5)
if Input_Voltage_Sweep(DMM,PS,VOLTAGE_SWEEP_RNG):
    print("INPUT VOLTAGE SWEEP: ", Fore.GREEN + "PASS")
else:
    print("INPUT VOLTAGE SWEEP: ", Fore.RED + "FAIL")

#safely close resources i hope
PS.write("*RST")
DMM.write("*RST")
RM.close()