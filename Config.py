#====================================================TESTING PARAMS====================================================#
#These are to be chosen in accordance with the DC_DC Converter Report 2.1
testing_cycle = "NON_SHIELDED"

#voltage and current parameters
IDEAL_INCOMING_VOLTAGE = 5.0
CALIBRATED_VOLTAGE_IN = 5.0
INITIAL_START_UP_VOLTAGE = [58.0,61.0]
INITIAL_START_UP_CURRENT = [0.035,0.033]
OUTPUT_VOLTAGE_COLD = [48.0,51.0]
INPUT_CURRENT_COLD = [0.025,0.027]

#DEBUG CONFIG SETTINGS
power_cycle_test = False     #turn this off during typical testing
MULTIPLE_POWER_CYCLES = False
debug = False #general debug to see more numbers during testing
timer_debug = True #timer negation for quenching times