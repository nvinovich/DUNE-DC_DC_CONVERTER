#====================================================TESTING PARAMS====================================================#
#These are to be chosen in accordance with the DC_DC Converter Report 2.1

#voltage and current parameters
IDEAL_INCOMING_VOLTAGE = 5.0    #baseline to shoot for when autocalibrating
voltage_jump_scale = 1.2    #multiplies how far the numerical diff. function jumps
INITIAL_START_UP_VOLTAGE = [58.0,61.0]
INITIAL_START_UP_CURRENT = [0.035,0.031] #for now, widening this as mr miller says its ok
OUTPUT_VOLTAGE_COLD = [48.0,51.0]
INPUT_CURRENT_COLD = [0.023,0.027] #same here

#DEBUG CONFIG SETTINGS
do_power_cycle_test, cold_only = True,True   #should be true, and cold only true if we only care about cold stats (we do)
pc_tests_hide = False #if False, FBD will try and retrieve power cycle statistics
hide_calibration_params = True

debug = False #general debug to see more numbers during testing
timer_debug, dtime = False, 0.5 #timer negation for quenching times, skips timers if True
snd = True #play timer completion sound