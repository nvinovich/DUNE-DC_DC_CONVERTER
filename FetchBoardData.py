import time
from colorama import Fore,init
import sys
from WorkbookCreator import *
init(autoreset=True)
#run this file to update data in your local spreadsheet

if input(Fore.MAGENTA + "Download full test data (1) or download specific board trace (2)? ") =="2":
    board_id = input(Fore.MAGENTA + "Enter board id: ")
    output_path = rf"C:\Users\StudentAdmin\Desktop\{board_id}.xlsx"

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
    print(Fore.LIGHTCYAN_EX + f"{board_id} TRACE DOWNLOAD COMPLETE")
    sys.exit(0)

conn = sqlite3.connect(DB_PATH)
output_file=r"C:\Users\StudentAdmin\Desktop\TESTONE.xlsx"
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
print(Fore.LIGHTCYAN_EX + "DOWNLOAD COMPLETE")