import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
DB_PATH = "dc_dc_temp3.db"
NSTAB_PATH = "dc_dc_nstabtemp.db"

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

            initial_temperature TEXT,
            secondary_calibration TEXT,
            input_current_output_voltage TEXT,
            output_step_load TEXT,
            input_step_voltage TEXT,
            output_noise_voltage TEXT,
            cold_start_up TEXT
        )
        """)
        conn.commit()

def init_nstab_db():
    '''creates secondary database for nominal load stabilization testing'''
    with sqlite3.connect(NSTAB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nstab (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id TEXT,
            timestamp TEXT,
            
            n0 REAL,
            n1 REAL,
            n2 REAL,
            n3 REAL,
            n4 REAL,
            n5 REAL,
            n6 REAL,
            n7 REAL,
            n8 REAL,
            n9 REAL

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
            initial_temperature,
            secondary_calibration,
            input_current_output_voltage,
            output_step_load,
            input_step_voltage,
            output_noise_voltage,
            cold_start_up
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)
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
            data["initial_temperature"],
            data["secondary_calibration"],
            data["input_current_output_voltage"],
            data["output_step_load"],
            data["input_step_voltage"],
            data["output_noise_voltage"],
            data["cold_start_up"],
        ))

def insert_nstab(data):
    '''this adds one set of board test data'''
    with sqlite3.connect(NSTAB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO nstab (
            board_id,
            timestamp,
            
            n0,
            n1,
            n2,
            n3,
            n4,
            n5,
            n6,
            n7,
            n8,
            n9)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,(
            data["board_id"],
            data["timestamp"],
            data["n0"],
            data["n1"],data["n2"],
            data["n3"],
            data["n4"],
            data["n5"],
            data["n6"], data["n7"],
            data["n8"],
            data["n9"])
        )


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


def export_nstab_to_excel(output_file=r"C:\Users\StudentAdmin\Desktop\NSTABTEMP1.xlsx"):
    '''i dont feel like making this whole thing modular right now, if we need more .xlsx in the future i will'''
    conn = sqlite3.connect(NSTAB_PATH)
    df = pd.read_sql_query("SELECT * FROM nstab", conn)
    conn.close()

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