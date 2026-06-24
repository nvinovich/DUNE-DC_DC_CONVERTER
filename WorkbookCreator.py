import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
DB_PATH = "dc_dc_temp1.db"

def init_db():
    '''this creates the database'''
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dc_dc_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id TEXT,
            timestamp TEXT,

            initial_voltage REAL,
            initial_current REAL,
            initial_start_up TEXT,
            input_voltage_sweep TEXT,
            nominal_load_performance TEXT,
            output_emi TEXT,

            initial_temperature TEXT,
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
            initial_voltage,
            initial_current,
            initial_start_up,
            input_voltage_sweep,
            nominal_load_performance,
            output_emi,
            initial_temperature,
            input_current_output_voltage,
            output_step_load,
            input_step_voltage,
            output_noise_voltage,
            cold_start_up
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
        """, (
            data["board_id"],
            datetime.now().isoformat(),
            data["initial_voltage"],
            data["initial_current"],
            data["initial_start_up"],
            data["input_voltage_sweep"],
            data["nominal_load_performance"],
            data["output_emi"],
            data["initial_temperature"],
            data["input_current_output_voltage"],
            data["output_step_load"],
            data["input_step_voltage"],
            data["output_noise_voltage"],
            data["cold_start_up"],
        ))


def export_to_excel(output_file=r"C:\Users\StudentAdmin\Desktop\TESTONE.xlsx"):
    '''creates temp excel file to read data'''
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM dc_dc_tests", conn)
    conn.close()

    df = df.rename(columns={
                   "board_id": "BOARD ID",
                   "timestamp": "TIMESTAMP",
            "initial_voltage": "INITIAL VOLTAGE",
            "initial_current": "INITIAL CURRENT",
            "initial_start_up": "INITIAL START UP",
            "input_voltage_sweep": "INPUT VOLTAGE SWEEP",
            "nominal_load_performance": "NOMINAL LOAD PERFORMANCE",
            "output_emi": "OUTPUT EMI",
            "initial_temperature": "INITIAL TEMPERATURE",
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