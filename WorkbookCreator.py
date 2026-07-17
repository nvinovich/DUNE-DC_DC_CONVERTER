import psycopg
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import json
from openpyxl.styles import Font, PatternFill, Alignment

#this will be a fairly major change away from sql lite to psygopg so i hope it works?
DB_INFO = {
    "host": "localhost",
    #server ip is: 172.17.106.247, replace with host if not using the server computer
    "dbname": "dcdc_tests",
    "user": "studadmin",
    "password": "password",
    "port": 5432
}
def get_connection():
    return psycopg.connect(**DB_INFO)

#can kill table with this command set, but please dont
#DROP TABLE dc_dc_tests;
#DROP TABLE board_traces;

#this whole routine is very touchy, it may cause issues for both db i/o and data collection if
#you touch this file
def init_db():
    '''this creates the database'''
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            
            
            CREATE TABLE IF NOT EXISTS dc_dc_tests (
                id SERIAL PRIMARY KEY,
                
                board_id TEXT UNIQUE,
                timestamp TIMESTAMP,
            
                calibrated_voltage TEXT,
                initial_voltage REAL,
                initial_current REAL,
                initial_start_up TEXT,
                input_voltage_sweep TEXT,
                nominal_load_performance TEXT,
                
                voltage_dev_warm REAL,
                mc_ave_vol REAL,
                mc_ave_cur REAL,
            
                secondary_calibration TEXT,
                initial_cold_voltage REAL,
                initial_cold_current REAL,
                input_current_output_voltage TEXT,
                output_step_load TEXT,
                input_step_voltage TEXT,
                cold_start_up TEXT,
                
                voltage_dev_cold REAL,
                mc_ave_vol_c REAL,
                mc_ave_cur_c REAL
            )
            """)
            conn.commit()

def insert_test(data):
    '''this adds one set of board test data'''

    #for now I am turning off the update and recording for output emi and cold noise
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO dc_dc_tests (
                board_id,
                timestamp,
                
                calibrated_voltage,
                initial_voltage,
                initial_current,
                initial_start_up,
                input_voltage_sweep,
                nominal_load_performance,
                
                voltage_dev_warm,
                mc_ave_vol,
                mc_ave_cur,
                
                secondary_calibration,
                initial_cold_voltage,
                initial_cold_current,
                input_current_output_voltage,
                output_step_load,
                input_step_voltage,
                cold_start_up,
                
                voltage_dev_cold,
                mc_ave_vol_c,
                mc_ave_cur_c
                
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                      %s,%s, %s, %s,%s,%s,%s,%s, %s,%s,%s, %s, %s)
            """, (
                data["board_id"],
                datetime.now(),

                data["calibrated_voltage"],
                data["initial_voltage"],
                data["initial_current"],
                data["initial_start_up"],
                data["input_voltage_sweep"],
                data["nominal_load_performance"],

                #adding even more fun statistics
                data["voltage_dev_warm"],
                data["mc_ave_vol"],
                data["mc_ave_cur"],
                
                data["secondary_calibration"],
                data["initial_cold_voltage"],
                data["initial_cold_current"],
                data["input_current_output_voltage"],
                data["output_step_load"],
                data["input_step_voltage"],
                data["cold_start_up"],

                data["voltage_dev_cold"],
                data["mc_ave_vol_c"],
                data["mc_ave_cur_c"],
            ))
            conn.commit()

def update_cold_test(data):
    '''updates cold test data'''

    with get_connection() as conn:
        with conn.cursor() as cursor:

        #for now I am turning off the update and recording for output emi and cold noise
            cursor.execute("""
            UPDATE dc_dc_tests
        
            SET
                voltage_dev_cold =%s,
                mc_ave_vol_c =%s,
                mc_ave_cur_c =%s,
                secondary_calibration = %s,
                initial_cold_voltage = %s,
                initial_cold_current = %s,
                input_current_output_voltage = %s,
                output_step_load = %s,
                input_step_voltage = %s,
                cold_start_up = %s,
                timestamp = %s
        
            WHERE board_id = %s
        
            """,
            (
                data["voltage_dev_cold"],
                data["mc_ave_vol_c"],
                data["mc_ave_cur_c"],

                data["secondary_calibration"],
                data["initial_cold_voltage"],
                data["initial_cold_current"],
                data["input_current_output_voltage"],
                data["output_step_load"],
                data["input_step_voltage"],
                data["cold_start_up"],
                datetime.now(),
                data["board_id"]
            ))

            conn.commit()

def init_trace_db():
    """trace data db"""
#multiple power cycle dump slots added
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS board_traces (
    id SERIAL PRIMARY KEY,

    board_id TEXT UNIQUE,
    timestamp TIMESTAMP,

    input_voltage_sweep_voltage_trace TEXT,
    input_voltage_sweep_current_trace TEXT,

    nominal_load_voltage_trace TEXT,
    nominal_load_current_trace TEXT,
                
    multiple_power_cycle_voltage TEXT,
    multiple_power_cycle_current TEXT,
    
    multiple_power_cycle_voltage_c TEXT,
    multiple_power_cycle_current_c TEXT,

    input_step_voltage_voltage_trace TEXT,
    input_step_voltage_current_trace TEXT,

    output_step_load_voltage_trace TEXT,
    output_step_load_current_trace TEXT,

    cold_startup_voltage_trace TEXT,
    cold_startup_current_trace TEXT
)
            """)
            conn.commit()

def insert_warm_traces(board_id,data):
    '''inserts new traces'''
        #updating the struct here to also track current

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           INSERT INTO board_traces
                           (board_id,
                            timestamp,
                            input_voltage_sweep_voltage_trace,
                            input_voltage_sweep_current_trace,
                            nominal_load_voltage_trace,
                            nominal_load_current_trace,
                            multiple_power_cycle_voltage,
                            multiple_power_cycle_current
                            )
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           """,
                           (
                               board_id,
                               datetime.now(),
                               json.dumps(data["input_voltage_sweep_voltage_trace"]),
                               json.dumps(data["input_voltage_sweep_current_trace"]),
                               json.dumps(data["nominal_load_voltage_trace"]),
                               json.dumps(data["nominal_load_current_trace"]),
                               #added dump slots for mc values
                               json.dumps(data["multiple_power_cycle_voltage"]),
                               json.dumps(data["multiple_power_cycle_current"]),

                           ))
            conn.commit()

def update_cold_traces(board_id,data
):
    #sorry for ultra strange db formatting throughout this, but shame on you for prying :[
    """Updates cold test traces for board trace schema version 2.0."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           UPDATE board_traces
                           SET cold_startup_voltage_trace=%s,
                               cold_startup_current_trace=%s,

                               output_step_load_voltage_trace=%s,
                               output_step_load_current_trace=%s,

                               input_step_voltage_voltage_trace=%s,
                               input_step_voltage_current_trace=%s,
                               
                                multiple_power_cycle_voltage_c=%s,
                                multiple_power_cycle_current_c=%s

                           WHERE board_id = %s
                           """,
                           (
                               json.dumps(data["cold_startup_voltage_trace"]),
                               json.dumps(data["cold_startup_current_trace"]),

                               json.dumps(data["output_step_load_voltage_trace"]),
                               json.dumps(data["output_step_load_current_trace"]),

                               json.dumps(data["input_step_voltage_voltage_trace"]),
                               json.dumps(data["input_step_voltage_current_trace"]),

                               json.dumps(data["multiple_power_cycle_voltage_c"]),
                               json.dumps(data["multiple_power_cycle_current_c"]),

                               board_id,
                           ))
            conn.commit()


def rename_board_id(old_id, new_id):
    '''updates an id to a new arg if it does not exist already'''
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT board_id
                FROM dc_dc_tests
                WHERE board_id = %s
            """, (new_id,))

            if cursor.fetchone():
                raise ValueError(f"Board ID {new_id} already exists.")

            cursor.execute("""
                UPDATE dc_dc_tests
                SET board_id = %s
                WHERE board_id = %s
            """, (new_id, old_id))

            tests_updated = cursor.rowcount

            cursor.execute("""
                UPDATE board_traces
                SET board_id = %s
                WHERE board_id = %s
            """, (new_id, old_id))

            traces_updated = cursor.rowcount

            conn.commit()

    print(
        f"Renamed {old_id} -> {new_id}\n"
        f"Test rows updated: {tests_updated}\n"
        f"Trace rows updated: {traces_updated}"
    )