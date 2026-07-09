import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import json
from openpyxl.styles import Font, PatternFill, Alignment
DB_PATH = "dc_dc_temp6.db"
TRACE_PATH = "dc_dc_temp_trace0.db"

#sorry for how this db pushing and fetching procedere works, it was a nightmare to figure out in the first place and so
#a lot of it is now done with the help of the dark arts

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

def export_to_excel(output_file=r"C:\Users\StudentAdmin\Desktop\TESTONE.xlsx"):
    '''creates temp excel file to read data'''
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM dc_dc_tests", conn)
    conn.close()

    df = df.rename(columns={
                   "board_id": "BOARD ID",
                   "timestamp": "TIMESTAMP",
            "calibrated_voltage": "CALIBRATED INPUT VOLTAGE",
            "initial_voltage": "INITIAL OUTPUT VOLTAGE",
            "initial_current": "INITIAL OUTPUT CURRENT",
            "initial_start_up": "INITIAL START UP",
            "input_voltage_sweep": "INPUT VOLTAGE SWEEP",
            "nominal_load_performance": "NOMINAL LOAD PERFORMANCE",
            "output_emi": "OUTPUT EMI",
            "secondary_calibration": "COLD CALIBRATION",
            "initial_cold_voltage":"INITIAL COLD VOLTAGE",
            "initial_cold_current":"INITIAL COLD CURRENT",
            "input_current_output_voltage": "INITIAL CURRENT OUTPUT VOLTAGE",
            "output_step_load": "OUTPUT STEP LOAD",
            "input_step_voltage": "INPUT STEP VOLTAGE",
            "output_noise_voltage": "OUTPUT NOISE VOLTAGE",
            "cold_start_up":  "COLD START UP",
    })

    df.to_excel(output_file, index=False)

    wb = load_workbook(output_file)
    ws = wb.active
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_len + 3

        #save formatted file
    wb.save(output_file)

def init_trace_db():
    """trace data db"""

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS board_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            board_id TEXT UNIQUE,
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
        VALUES (?,?,?,?,?)
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
            input_step_voltage_trace=?,

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

    # Convert SQL row into dictionary
    data = dict(zip(columns, row))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        for test_name, trace_json in data.items():

            # Only process trace columns
            if test_name.endswith("_trace") and trace_json is not None:

                trace = json.loads(trace_json)

                df = pd.DataFrame({
                    "Sample": range(len(trace)),
                    "Value": trace
                })

                # Excel sheet names max length is 31 chars
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