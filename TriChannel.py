import sys
import time
import pyvisa
from colorama import init, Fore, Back, Style
init(autoreset=True)


#Check for good multimeter and power supply connections
print("Checking for resources...")
RM = pyvisa.ResourceManager()
resources = RM.list_resources()

print(resources)

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

#reset all resources
DMM.write("*RST")
DMM.write("*CLS")
DMM.write("SENS:FUNC 'VOLT:DC'")
DMM.write("VOLT:DC:RANG 100")
PS.write("*RST")
#set both channel 1 and 2 to 5 volt
PS.write("INST CH1")
PS.write("VOLT 5")
PS.write("CURR 0.05")
PS.write("OUTP ON")
PS.write("INST CH2")
PS.write("VOLT 5")
PS.write("CURR 0.25")
PS.write("OUTP ON")

PS.query("*OPC?")   #checks if the power supply is all correct
print("power have :)")

#open channel 1 and read twice

DMM.write("ROUT:MULT:CLOS (@3)")
time.sleep(0.5)
print(DMM.query("READ?"))
#and close
DMM.write("ROUT:MULT:OPEN (@3)")

time.sleep(2)
PS.write("*RST")

RM.close()