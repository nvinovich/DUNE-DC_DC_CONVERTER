import psycopg
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import json
from openpyxl.styles import Font, PatternFill, Alignment
#this will be a fairly major change away from sql lite to psygopg so i hope it works?
DB_INFO = {
    "host": "localhost",
    "dbname": "dcdc_tests",
    "user": "studadmin",
    "password": "password",
    "port": 5432
}
def get_connection():
    return psycopg.connect(**DB_INFO)

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
            
                secondary_calibration TEXT,
                initial_cold_voltage REAL,
                initial_cold_current REAL,
                input_current_output_voltage TEXT,
                output_step_load TEXT,
                input_step_voltage TEXT,
                cold_start_up TEXT
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
                secondary_calibration,
                initial_cold_voltage,
                initial_cold_current,
                input_current_output_voltage,
                output_step_load,
                input_step_voltage,
                cold_start_up
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s, %s, %s,%s,%s,%s)
            """, (
                data["board_id"],
                datetime.now(),
                data["calibrated_voltage"],
                data["initial_voltage"],
                data["initial_current"],
                data["initial_start_up"],
                data["input_voltage_sweep"],
                data["nominal_load_performance"],
                data["secondary_calibration"],
                data["initial_cold_voltage"],
                data["initial_cold_current"],
                data["input_current_output_voltage"],
                data["output_step_load"],
                data["input_step_voltage"],
                data["cold_start_up"],
            ))

def update_cold_test(data):
    '''updates cold test data'''

    with get_connection() as conn:
        with conn.cursor() as cursor:

        #for now I am turning off the update and recording for output emi and cold noise
            cursor.execute("""
            UPDATE dc_dc_tests
        
            SET
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

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS board_traces (
                id SERIAL PRIMARY KEY,
            
                board_id TEXT UNIQUE,
                timestamp TIMESTAMP,
            
                input_voltage_sweep_trace TEXT,
                nominal_load_trace TEXT,         
                input_step_voltage_trace TEXT,
                output_step_load_trace TEXT,
                cold_startup_trace TEXT
            )
            """)
            conn.commit()

def insert_warm_traces(board_id, sweep, nominal):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO board_traces
            (
                board_id,
                timestamp,
                input_voltage_sweep_trace,
                nominal_load_trace
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                board_id,
                datetime.now(),
                json.dumps(sweep),
                json.dumps(nominal)
            ))
            conn.commit()

def update_cold_traces(board_id, cold, step, input_step):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE board_traces
            
            SET
                cold_startup_trace=%s,
                output_step_load_trace=%s,
                input_step_voltage_trace=%s
            
            WHERE board_id=%s
            """,
            (
                json.dumps(cold),
                json.dumps(step),
                json.dumps(input_step),
                board_id
            ))
            conn.commit()