import os
import time
from colorama import Fore,init
import sys
import subprocess
from WorkbookCreator import *
init(autoreset=True)

#Run this file to update data in your local spreadsheet, but replace the following parameter with system desktop path or
#other desired download destination:
DD = rf"C:\Users\StudentAdmin\Desktop"
XLSX_NAME= "TESTS"

def Trace_Getter(TRACE_PATH,board_id,output_path):
    '''Writes the data for the trace of a board to a file'''
    #again im very iffy about sql atm but this should work mostly fine
    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT *
                       FROM board_traces
                       WHERE board_id = ?
                       """, (board_id,))

        row = cursor.fetchone()

        if row is None:
            sys.exit(f"No trace data found for board {board_id}")

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
    print(Fore.LIGHTCYAN_EX + f"{board_id} TRACE DOWNLOAD COMPLETE")

def Export_All_Traces(TRACE_PATH, output_folder):
    """Calls Trace_Getter() for every board in the trace database"""

    with sqlite3.connect(TRACE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT board_id FROM board_traces")
        board_ids = [row[0] for row in cursor.fetchall()]
    if not board_ids:
        sys.exit("No trace data found.")

    for board_id in board_ids:
        output_path = os.path.join(
            output_folder,
            f"{board_id}_Trace_Data.xlsx"
        )
        Trace_Getter(TRACE_PATH, board_id, output_path)

    print(Fore.GREEN + "ALL TRACE DOWNLOADS COMPLETE")

def Test_Results_Getter(DB_PATH,DD,XLSX_NAME) -> None:
    '''Writes out the test data for full db onto one xlsx file'''
    conn = sqlite3.connect(DB_PATH)
    output_file = DD + rf"\{XLSX_NAME}.xlsx"
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
        "initial_cold_voltage": "INITIAL COLD VOLTAGE",
        "initial_cold_current": "INITIAL COLD CURRENT",
        "input_current_output_voltage": "INITIAL CURRENT OUTPUT VOLTAGE",
        "output_step_load": "OUTPUT STEP LOAD",
        "input_step_voltage": "INPUT STEP VOLTAGE",
        "output_noise_voltage": "OUTPUT NOISE VOLTAGE",
        "cold_start_up": "COLD START UP",
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
        # save formatted file
    wb.save(output_file)

TRCHOICE = input(Fore.MAGENTA + ">Download full test data (1)\n>Download specific board trace (2) \n"
                        ">Download full SQL image (3)\n"
                        "Choose a readback option: ")

if TRCHOICE == "2":
    #baord choice saver
    board_id = input(Fore.MAGENTA + "Enter board id: ")
    output_path = DD + rf"\{board_id}.xlsx"
    Trace_Getter(TRACE_PATH,board_id,output_path)

elif TRCHOICE == "1":
    #this path saves the full test data so far
    Test_Results_Getter(DB_PATH,DD,XLSX_NAME)
    print(Fore.LIGHTCYAN_EX + "TEST DOWNLOAD COMPLETE")

elif TRCHOICE == "3":
    #needs usb or other external mount at D
    drive_letter = "D"
    if os.path.exists(f"{drive_letter.upper()}:\\"):
        print(f"{drive_letter.upper()}: DRIVE FOUND")

        folder_path = os.path.join(f"{drive_letter.upper()}:\\", "DB_IMAGE")

        try:
            #this is the actual writing setp, maybe I should prompt this for every n tests
            os.makedirs(folder_path, exist_ok=True)
            Test_Results_Getter(DB_PATH,folder_path,XLSX_NAME)
            print(Fore.GREEN + "TEST DOWNLOAD COMPLETE")
            #now that this saves, lets give it a moment and then write all trace data, this may take some time
            time.sleep(0.2)
            Export_All_Traces(TRACE_PATH,folder_path)

        #just some generic error throws I stole that should be helpful
        except PermissionError:
            print("Error: No permission to write to this drive.")
        except OSError as e:
            print(f"Error creating folder or file: {e}")
    else:
        print(f"{drive_letter.upper()}: DRIVE NOT FOUND.")

else:
    sys.exit("INVALID SELECTION")