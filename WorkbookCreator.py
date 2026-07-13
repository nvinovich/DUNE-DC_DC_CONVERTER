import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import json
from openpyxl.styles import Font, PatternFill, Alignment
DB_PATH = "dc_dc_temp6.db"
TRACE_PATH = "dc_dc_temp_trace1.db"

#this whole routine is very touchy, it may cause issues for both db i/o and data collection if
#you touch this file
def init_db():
    '''this creates the database'''
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dc_dc_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id TEXT,
            timestamp TEXT,

            calibrated_voltage REAL,
            initial_voltage REAL,
            initial_current REAL,
            initial_start_up TEXT,
            input_voltage_sweep TEXT,
            nominal_load_performance TEXT,
            output_emi TEXT,

            secondary_calibration REAL,
            initial_cold_voltage REAL,
            inital_cold_current REAL,
            input_current_output_voltage TEXT,
            output_step_load TEXT,
            input_step_voltage TEXT,
            output_noise_voltage TEXT,
            cold_start_up TEXT
        )
        """)
        conn.commit()

def insert_test(data):
    '''this adds one set of board test data'''
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

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
            output_emi,
            secondary_calibration,
            initial_cold_voltage,
            inital_cold_current,
            input_current_output_voltage,
            output_step_load,
            input_step_voltage,
            output_noise_voltage,
            cold_start_up
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?, ?, ?,?,?,?)
        """, (
            data["board_id"],
            datetime.now().isoformat(),
            data["calibrated_voltage"],
            data["initial_voltage"],
            data["initial_current"],
            data["initial_start_up"],
            data["input_voltage_sweep"],
            data["nominal_load_performance"],
            data["output_emi"],
            data["secondary_calibration"],
            data["initial_cold_voltage"],
            data["initial_cold_current"],
            data["input_current_output_voltage"],
            data["output_step_load"],
            data["input_step_voltage"],
            data["output_noise_voltage"],
            data["cold_start_up"],
        ))

def update_cold_test(data):
    '''updates cold test data'''

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE dc_dc_tests

        SET
            secondary_calibration = ?,
            initial_cold_voltage = ?,
            inital_cold_current = ?,
            input_current_output_voltage = ?,
            output_step_load = ?,
            input_step_voltage = ?,
            output_noise_voltage = ?,
            cold_start_up = ?,
            timestamp = ?

        WHERE board_id = ?

        """,
        (
            data["secondary_calibration"],
            data["initial_cold_voltage"],
            data["initial_cold_current"],
            data["input_current_output_voltage"],
            data["output_step_load"],
            data["input_step_voltage"],
            data["output_noise_voltage"],
            data["cold_start_up"],
            datetime.now().isoformat(),
            data["board_id"]
        ))

        conn.commit()

def init_trace_db():
    """trace data db"""

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS board_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            board_id TEXT,
            timestamp TEXT,

            input_voltage_sweep_trace TEXT,
            nominal_load_trace TEXT,         
            input_step_voltage_trace TEXT,
            output_step_load_trace TEXT,
            cold_startup_trace TEXT
        )
        """)
        conn.commit()

def insert_warm_traces(board_id, sweep, nominal):

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO board_traces
        (
            board_id,
            timestamp,
            input_voltage_sweep_trace,
            nominal_load_trace
        )
        VALUES (?,?,?,?)
        """,
        (
            board_id,
            datetime.now().isoformat(),
            json.dumps(sweep),
            json.dumps(nominal)
        ))
        conn.commit()

def update_cold_traces(board_id, cold, step, input_step):

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE board_traces

        SET
            cold_startup_trace=?,
            output_step_load_trace=?,
            input_step_voltage_trace=?

        WHERE board_id=?
        """,
        (
            json.dumps(cold),
            json.dumps(step),
            json.dumps(input_step),
            board_id
        ))
        conn.commit()

def export_board_trace_to_excel(board_id, output_path=None):

    if output_path is None:
        output_path = f"{board_id}.xlsx"

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM board_traces
        WHERE board_id = ?
        """, (board_id,))

        row = cursor.fetchone()

        if row is None:
            print(f"No trace data found for board {board_id}")
            return

        columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, row))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for test_name, trace_json in data.items():
            if test_name.endswith("_trace") and trace_json is not None:

                trace = json.loads(trace_json)
                df = pd.DataFrame({
                    "Sample": range(len(trace)),
                    "Value": trace
                })
                sheet_name = test_name[:31]
                df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )
    wb = load_workbook(output_path)

    for ws in wb:
        for col in ws.columns:
            max_length = max(
                len(str(cell.value)) if cell.value else 0
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = max_length + 3
    wb.save(output_path)
    print(f"Exported {board_id} traces to {output_path}")