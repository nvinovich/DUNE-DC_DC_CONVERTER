import sys

import psycopg
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import json
from openpyxl.styles import Font, PatternFill, Alignment

#this will be a fairly major change away from sql lite to psygopg so i hope it works?
DB_INFO = {
    "host": "localhost",
    #server ip is: 172.17.106.247, replace localhost with this if not using the server computer
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
                
                board_id TEXT NOT NULL,
                timestamp TIMESTAMP,
                phase TEXT NOT NULL,
                testing_admin TEXT,
            
                calibrated_voltage TEXT,
                initial_voltage TEXT,
                initial_current TEXT,
                load_voltage TEXT,
                load_current TEXT,
                initial_start_up TEXT,
                input_voltage_sweep_w TEXT,
                sweep_min_max_w TEXT,
                nominal_load_performance TEXT,
                
                voltage_dev_warm TEXT,
                mc_ave_vol TEXT,
                mc_ave_cur TEXT,
            
                secondary_calibration TEXT,
                initial_cold_voltage TEXT,
                initial_cold_current TEXT,
                load_voltage_c TEXT,
                load_current_c TEXT,
                input_current_output_voltage TEXT,
                output_step_load TEXT,
                input_step_voltage TEXT,
                input_voltage_sweep_c TEXT,
                sweep_min_max_c TEXT,
                cold_start_up TEXT,
                
                voltage_dev_cold TEXT,
                mc_ave_vol_c TEXT,
                mc_ave_cur_c TEXT,
                
                shipment TEXT,
                
                 UNIQUE (board_id, phase)
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
                phase,
                testing_admin,
                
                calibrated_voltage,
                initial_voltage,
                initial_current,
                load_voltage,
                load_current,
                initial_start_up,
                input_voltage_sweep_w,
                sweep_min_max_w,
                nominal_load_performance,
                
                voltage_dev_warm,
                mc_ave_vol,
                mc_ave_cur,
                
                secondary_calibration,
                initial_cold_voltage,
                initial_cold_current,
                load_voltage_c,
                load_current_c,
                input_current_output_voltage,
                output_step_load,
                input_step_voltage,
                input_voltage_sweep_c,
                sweep_min_max_c,
                cold_start_up,
                
                voltage_dev_cold,
                mc_ave_vol_c,
                mc_ave_cur_c,
                
                shipment
                
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s,
                      %s, %s, %s, %s, %s, %s, %s, %s,%s,%s, 
                      %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,
                      %s)
            """, (      #fixed this :)
                data["board_id"],
                datetime.now(),
                data["phase"],
                data["testing_admin"],

                data["calibrated_voltage"],
                data["initial_voltage"],
                data["initial_current"],
                data["load_voltage"],
                data["load_current"],

                data["initial_start_up"],
                data["input_voltage_sweep_w"],
                data["sweep_min_max_w"],
                data["nominal_load_performance"],

                #adding even more fun statistics
                data["voltage_dev_warm"],
                data["mc_ave_vol"],
                data["mc_ave_cur"],
                
                data["secondary_calibration"],
                data["initial_cold_voltage"],
                data["initial_cold_current"],
                data["load_voltage_c"],
                data["load_current_c"],

                data["input_current_output_voltage"],
                data["output_step_load"],
                data["input_step_voltage"],
                data["input_voltage_sweep_c"],
                data["sweep_min_max_c"],
                data["cold_start_up"],

                data["voltage_dev_cold"],
                data["mc_ave_vol_c"],
                data["mc_ave_cur_c"],

                "",
            ))
            conn.commit()

def update_cold_test(data):
    '''updates cold test data'''

    with get_connection() as conn:
        with conn.cursor() as cursor:

        #updating to have collumns for the new tesing battery
            cursor.execute("""
            UPDATE dc_dc_tests
        
            SET
                voltage_dev_cold =%s,
                mc_ave_vol_c =%s,
                mc_ave_cur_c =%s,
                secondary_calibration = %s,
                initial_cold_voltage = %s,
                initial_cold_current = %s,
                load_voltage_c = %s,
                load_current_c = %s,
                input_current_output_voltage = %s,
                output_step_load = %s,
                input_step_voltage = %s,
                input_voltage_sweep_c = %s,
                sweep_min_max_c = %s,
                cold_start_up = %s,
                timestamp = %s
        
            WHERE board_id = %s
            AND phase = %s
        
            """,
                           #god  i hate SQL
            (
                data["voltage_dev_cold"],
                data["mc_ave_vol_c"],
                data["mc_ave_cur_c"],

                data["secondary_calibration"],
                data["initial_cold_voltage"],
                data["initial_cold_current"],
                data["load_voltage_c"],
                data["load_current_c"],

                data["input_current_output_voltage"],
                data["output_step_load"],
                data["input_step_voltage"],
                data["input_voltage_sweep_c"],
                data["sweep_min_max_c"],
                data["cold_start_up"],
                datetime.now(),
                data["board_id"],
                data["phase"]
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

    board_id TEXT NOT NULL,
    timestamp TIMESTAMP,
    phase TEXT NOT NULL,

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
    
    input_voltage_sweep_voltage_trace_c TEXT,
    input_voltage_sweep_current_trace_c TEXT,

    cold_startup_voltage_trace TEXT,
    cold_startup_current_trace TEXT,
    
    UNIQUE (board_id, phase)
)
            """)
            conn.commit()

def insert_warm_traces(board_id,phase,data):
    '''inserts new traces'''
        #updating the struct here to also track current

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           INSERT INTO board_traces
                           (board_id,
                            timestamp,
                            phase,
                            input_voltage_sweep_voltage_trace,
                            input_voltage_sweep_current_trace,
                            nominal_load_voltage_trace,
                            nominal_load_current_trace,
                            multiple_power_cycle_voltage,
                            multiple_power_cycle_current
                            )
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
                           """,
                           (
                               board_id,
                               datetime.now(),
                               phase,
                               json.dumps(data["input_voltage_sweep_voltage_trace"]),
                               json.dumps(data["input_voltage_sweep_current_trace"]),
                               json.dumps(data["nominal_load_voltage_trace"]),
                               json.dumps(data["nominal_load_current_trace"]),
                               #added dump slots for mc values
                               json.dumps(data["multiple_power_cycle_voltage"]),
                               json.dumps(data["multiple_power_cycle_current"]),

                           ))
            conn.commit()

def update_cold_traces(board_id,phase,data
):
    #sorry for ultra strange db formatting throughout this, but shame on you for prying :[
    """updates cold test traces for board trace schema version 2.0."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                           UPDATE board_traces
                           SET cold_startup_voltage_trace=%s,
                               cold_startup_current_trace=%s,

                               output_step_load_voltage_trace=%s,
                               output_step_load_current_trace=%s,
                               
                               input_voltage_sweep_voltage_trace_c =%s,
                               input_voltage_sweep_current_trace_c =%s,

                               input_step_voltage_voltage_trace=%s,
                               input_step_voltage_current_trace=%s,
                               
                                multiple_power_cycle_voltage_c=%s,
                                multiple_power_cycle_current_c=%s

                           WHERE board_id = %s AND phase = %s
                           """,
                           (
                               json.dumps(data["cold_startup_voltage_trace"]),
                               json.dumps(data["cold_startup_current_trace"]),

                               json.dumps(data["output_step_load_voltage_trace"]),
                               json.dumps(data["output_step_load_current_trace"]),

                               json.dumps(data["input_voltage_sweep_voltage_trace_c"]),
                               json.dumps(data["input_voltage_sweep_current_trace_c"]),

                               json.dumps(data["input_step_voltage_voltage_trace"]),
                               json.dumps(data["input_step_voltage_current_trace"]),

                               json.dumps(data["multiple_power_cycle_voltage_c"]),
                               json.dumps(data["multiple_power_cycle_current_c"]),

                               board_id,phase,
                           ))
            conn.commit()


def rename_board_id(old_id, new_id, phase):
    """
    updates an id to a new arg if it does not exist already
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT board_id
                FROM dc_dc_tests
                WHERE board_id=%s
                AND phase=%s
            """, (new_id, phase))
            if cursor.fetchone():
                raise ValueError(f"Board ID {new_id} already exists.")
            cursor.execute("""
                UPDATE dc_dc_tests
                SET board_id = %s
                WHERE board_id=%s
                AND phase=%s
            """, (new_id, old_id, phase))
            tests_updated = cursor.rowcount
            cursor.execute("""
                UPDATE board_traces
                SET board_id = %s
                WHERE board_id=%s
                AND phase=%s
            """, (new_id, old_id, phase))
            traces_updated = cursor.rowcount
            conn.commit()
    print(
        f"Renamed {old_id} -> {new_id}\n"
        f"Test rows updated: {tests_updated}\n"
        f"Trace rows updated: {traces_updated}"
    )

def init_phase_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_phases (
                    id SERIAL PRIMARY KEY,
                    phase TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

def add_phase(phase_name):
    """
    Adds a new allowed testing phase.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT phase
                FROM test_phases
                WHERE phase = %s
            """, (phase_name,))
            #if phase name colision, let me rename it
            if cursor.fetchone():
                print(
                    f"Phase '{phase_name}' already exists.")
                if input("Rename phase?").lower() =='y':
                    name2 = input("Input new phase name ")
                    cursor.execute("""
                                    UPDATE test_phases
                                    SET phase = %s
                                    WHERE phase = %s
                                """, (name2, phase_name))

                    conn.commit()
                    sys.exit()
                else:
                    sys.exit()
            cursor.execute("""
                INSERT INTO test_phases (phase)
                VALUES (%s)
            """, (phase_name,))

            conn.commit()

    print(f"Added new phase: {phase_name}")

def delete_empty_phases():
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM test_phases tp
                WHERE tp.phase NOT IN (
                    SELECT DISTINCT phase
                    FROM dc_dc_tests
                )
                AND tp.phase NOT IN (
                    SELECT DISTINCT phase
                    FROM board_traces
                )
                RETURNING phase
            """)

            deleted = [row[0] for row in cursor.fetchall()]
            conn.commit()

    if deleted:
        print("Deleted empty phases:")
        for phase in deleted:
            print(f"  - {phase}")
    else:
        print("No empty phases found.")

def Delete_Board_Phase_Entry(board_id, phase):
    """
    Deletes a board entry for a specific testing phase, allows for bad inputation deletion in the case
    that only traces are entered
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:

            #check if entry exists
            cursor.execute("""
                SELECT *
                FROM dc_dc_tests
                WHERE board_id = %s
                  AND phase = %s
            """, (board_id, phase))

            entry = cursor.fetchone()
            entry2 = False

            if not entry:
                # check if entry exists in traces at least
                cursor.execute("""
                    SELECT *
                    FROM board_traces
                    WHERE board_id = %s
                      AND phase = %s
                """, (board_id, phase))

                entry2 = cursor.fetchone()
                if not entry2:
                    print(f"No entry found for Board {board_id} in phase '{phase}'")
                    return

            print(f"Board ID: {board_id}")
            print(f"Phase: {phase}")
            print(entry)

            confirm = input("\nAre you sure? (y/n): ")

            if confirm.lower() != "y":
                print("Deletion cancelled.")
                return

            #delete traces for this board and phase, or phase only if only possible
            cursor.execute("""
                DELETE FROM board_traces
                WHERE board_id = %s
                  AND phase = %s
            """, (board_id, phase))
            trace_count = cursor.rowcount

            #doesnt do if only trace exists
            if entry:
                cursor.execute("""
                    DELETE FROM dc_dc_tests
                    WHERE board_id = %s
                  AND phase = %s
                """, (board_id, phase))
                test_count = cursor.rowcount

            conn.commit()

            print("\nDeletion complete:")
            if entry:
                print(f"Deleted {test_count} test entry(s)")
            if entry2:
                print(f"Deleted {trace_count} trace entry(s)")