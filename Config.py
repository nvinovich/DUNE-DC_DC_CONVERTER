#====================================================TESTING PARAMS====================================================#
#These are to be chosen in accordance with the DC_DC Converter Report 2.1

#voltage and current parameters
IDEAL_INCOMING_VOLTAGE = 5.0
CALIBRATED_VOLTAGE_IN = 5.0
INITIAL_START_UP_VOLTAGE = [58.0,61.0]
INITIAL_START_UP_CURRENT = [0.035,0.031] #for now, widening this as mr miller says its ok
OUTPUT_VOLTAGE_COLD = [48.0,51.0]
INPUT_CURRENT_COLD = [0.023,0.027] #same here

#DEBUG CONFIG SETTINGS
power_cycle_test = False     #turn this off during typical testing
MULTIPLE_POWER_CYCLES = False
pc_tests_hide = True #if False, FBD will try and retrieve power cycle statistics
hide_calibration_params = True

debug = False #general debug to see more numbers during testing
timer_debug, dtime = False, 0.5 #timer negation for quenching times
snd = True #play timer completion sound