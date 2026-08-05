import os
import time
from colorama import Fore,init
import psycopg
import sys
import subprocess

from Utilities import convert_scientific_to_float
from WorkbookCreator import *
import matplotlib.pyplot as mp
import numpy as np
init(autoreset=True)

#updates here too
DB_INFO = {
    "host": "localhost",
    "dbname": "dcdc_tests",
    "user": "studadmin",
    "password": "password",
    "port": 5432
}
def get_connection():
    return psycopg.connect(**DB_INFO)

#Run this file to update data in your local spreadsheet, but replace the following parameter with system desktop path or
#other desired download destination:
DD = rf"C:\Users\StudentAdmin\Desktop"
XLSX_NAME= "TESTS"

#clutter hiding options
pc_tests_hide = True
if pc_tests_hide:
    hide_sheets = ["Multiple Power Cycle Cold","Multiple Power Cycle Warm"]
else:
    hide_sheets = []

def Trace_Getter(board_id, phase, output_path):
    '''Writes the data for the trace of a board to a file'''
    #again im very iffy about sql atm but this should work mostly fine
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM board_traces
                WHERE board_id = %s
                  AND phase = %s
            """, (board_id, phase))

            row = cursor.fetchone()

            if row is None:
                sys.exit(f"No trace data found for board {board_id}")

            columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))

        trace_pairs = {
            "Input Voltage Sweep": (
                "input_voltage_sweep_voltage_trace",
                "input_voltage_sweep_current_trace"
            ),
            "Nominal Load": (
                "nominal_load_voltage_trace",
                "nominal_load_current_trace"
            ),
            "Multiple Power Cycle Warm": (
                "multiple_power_cycle_voltage",
                "multiple_power_cycle_current"
            ),
            "Multiple Power Cycle Cold": (
                "multiple_power_cycle_voltage_c",
                "multiple_power_cycle_current_c"
            ),
            "Input Step Voltage": (
                "input_step_voltage_voltage_trace",
                "input_step_voltage_current_trace"
            ),
            "Output Step Load": (
                "output_step_load_voltage_trace",
                "output_step_load_current_trace"
            ),
            "Cold Start Up": (
                "cold_startup_voltage_trace",
                "cold_startup_current_trace"
            )
        }

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

            for name, (vol_col, cur_col) in trace_pairs.items():
                #hide clutter sheets if needed
                if name in hide_sheets:
                    continue

                voltage = data.get(vol_col)
                current = data.get(cur_col)

                if voltage is not None:

                    voltage = json.loads(voltage)

                    output = {
                        "Sample": range(len(voltage)),
                        "Voltage": voltage
                    }

                    if current is not None:
                        current = json.loads(current)

                        # Only add current if it matches voltage length
                        if len(current) == len(voltage):
                            output["Current"] = current

                    df = pd.DataFrame(output)

                    df = df.map(convert_scientific_to_float)

                    df.to_excel(
                        writer,
                        sheet_name=name[:31],
                        index=False
                    )

   #scientific notation
                    ws = writer.sheets[name[:31]]
                    for cell in ws["B"][1:]:
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = "0.00000E+00"
                    if "Current" in output:
                        for cell in ws["C"][1:]:
                            if isinstance(cell.value, (int, float)):
                                cell.number_format = "0.00000E+00"

        wb = load_workbook(output_path)

        for ws in wb:
            for col in ws.columns:
                max_length = max(
                    len(str(cell.value)) if cell.value else 0
                    for cell in col
                )
                ws.column_dimensions[col[0].column_letter].width = max_length + 50
        wb.save(output_path)
        print(Fore.LIGHTCYAN_EX + f"{board_id} TRACE DOWNLOAD COMPLETE")

def Export_All_Traces(output_folder, phase):
    """Exports every board trace to its own xlsx file by iteratively calling Trace_Getter()"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT board_id
                FROM board_traces
                WHERE phase = %s
                ORDER BY
    CASE
        WHEN board_id ~ '^[0-9]+$'
        THEN board_id::INTEGER
        ELSE NULL
    END,
    board_id
            """, (phase,))

            board_ids = [
                row[0]
                for row in cursor.fetchall()
            ]

    if not board_ids:
        sys.exit("No trace data found.")
    for board_id in board_ids:
        output_path = os.path.join(
            output_folder,
            f"{board_id}_Trace_Data.xlsx"
        )
        Trace_Getter(board_id, phase,output_path)

    print(Fore.GREEN + "ALL TRACE DOWNLOADS COMPLETE")

def Select_Phase():
    """
    Displays all allowed testing phases and returns the one selected by the user.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT phase
                FROM test_phases
                ORDER BY phase
            """)

            phases = [row[0] for row in cursor.fetchall()]

    if not phases:
        raise ValueError("No testing phases found.")
    print("\nAvailable Testing Phases")

    for i, phase in enumerate(phases, start=1):
        print(f"{i}) {phase}")

    while True:
        try:
            choice = int(input(Fore.MAGENTA + "Select phase (by number): "))

            if 1 <= choice <= len(phases):
                return phases[choice - 1]

            print("Invalid selection.")

        except ValueError:
            print("Enter a number.")

def Test_Results_Getter(DD, XLSX_NAME,phase) -> None:
    '''Writes out the test data for full database onto one xlsx file'''

    output_file = DD + rf"\{XLSX_NAME}.xlsx"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
FROM dc_dc_tests
WHERE phase = %s
ORDER BY
    CASE
        WHEN board_id ~ '^[0-9]+$'
        THEN board_id::INTEGER
        ELSE NULL
    END,
    board_id
            """, (phase,))
            rows = cursor.fetchall()

            columns = [
                desc[0]
                for desc in cursor.description
            ]

    df = pd.DataFrame(
        rows,
        columns=columns
    )

    #timestamp reformatting
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

    if pc_tests_hide:
        debug_remove = [
            "id",
            "phase",
            "voltage_dev_warm",
            "voltage_dev_cold",
            "mc_ave_vol",
            "mc_ave_cur",
            "mc_ave_vol_c",
            "mc_ave_cur_c",
        ]

        df = df.drop(columns=debug_remove, errors="ignore")

    df = df.rename(columns={
        "board_id": "BOARD ID",
        "timestamp": "TIMESTAMP",
        "testing_admin": "TEST ADMIN",

        "calibrated_voltage": "CALIBRATED INPUT VOLTAGE (WARM)",
        "initial_voltage": "INITIAL OUTPUT VOLTAGE",
        "initial_current": "INITIAL OUTPUT CURRENT",
        "initial_start_up": "INITIAL START UP",
        "input_voltage_sweep": "INPUT VOLTAGE SWEEP",
        "nominal_load_performance": "NOMINAL LOAD PERFORMANCE",

        "voltage_dev_warm": "WARM VOLTAGE DEVIATION",
        "mc_ave_vol": "WARM POWERCYCLE AVE VOLTAGE",
        "mc_ave_cur": "WARM POWERCYCLE AVE CURRENT",

        "secondary_calibration": "CALIBRATED INPUT VOLTAGE (COLD)",
        "initial_cold_voltage": "INITIAL COLD VOLTAGE",
        "initial_cold_current": "INITIAL COLD CURRENT",
        "input_current_output_voltage": "INITIAL CURRENT OUTPUT VOLTAGE",
        "output_step_load": "OUTPUT STEP LOAD",
        "input_step_voltage": "INPUT STEP VOLTAGE",
        "cold_start_up": "COLD START UP",

        "voltage_dev_cold": "COLD VOLTAGE DEVIATION",
        "mc_ave_vol_c": "COLD POWERCYCLE AVE VOLTAGE",
        "mc_ave_cur_c": "COLD POWERCYCLE AVE CURRENT",
    })
    df.to_excel(output_file, index=False)
    wb = load_workbook(output_file)
    ws = wb.active
    #preserves visible testing categories
    ws.freeze_panes = "A2"

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE"  # light green
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True)
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )
    grey_fill = PatternFill(
            fill_type="solid",
            fgColor="E7E6E6"
        )

    white_fill = PatternFill(
            fill_type="solid",
            fgColor="FFFFFF"
        )

    for row in range(2, ws.max_row + 1):

        fill = grey_fill if row % 2 == 0 else white_fill

        for cell in ws[row]:
            cell.fill = fill

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_len = max(
                    max_len,
                    len(str(cell.value))
                )

        ws.column_dimensions[col_letter].width = max_len + 3

    wb.save(output_file)

def Voltage_Histogram(board_id,phase,xrs,temp="(Warm)",
                      trace_column="multiple_power_cycle_voltage",
                      output_folder=r"C:\Users\StudentAdmin\Desktop"):
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(f"""
                SELECT {trace_column}
                FROM board_traces
                WHERE board_id = %s
            """, (board_id,))

            row = cursor.fetchone()

    if row is None:
        print(f"No data found for board {board_id}")
        return

    if row[0] is None:
        print(f"{trace_column} is empty for board {board_id}")
        return

    pc_vols = json.loads(row[0])

    avg_voltage = np.mean(pc_vols)
    std_voltage = np.std(pc_vols)

    mp.figure(figsize=(8,5))

    mp.hist(
        pc_vols,
        bins=50
    )
    #added in clearance zone plotting
    mp.axvspan(xrs[0],xrs[1], alpha=0.35, color="grey", label="Ideal Operating Range")

    mp.legend(
        title=f"Ave = {avg_voltage:.5f} V\nStDev = {std_voltage:.5f} V"
    )

    mp.title(f"Voltage Behavior for {board_id}" + temp)
    mp.xlabel("Voltage (V)")
    mp.ylabel("Samples at Voltage")
    mp.grid(True)

    filename = f"{board_id}_{trace_column}.png"
    save_path = os.path.join(output_folder, filename)

    mp.savefig(save_path, dpi=300, bbox_inches="tight")
    mp.close()

    print(Fore.GREEN + f"Histogram saved to:\n{save_path}")

if __name__ == "__main__":
    TRCHOICE = input(Fore.MAGENTA + ">Download phase SQL data to PC (1)\n"
                                    ">Download phase SQL data to external drive (2)\n"
                                    ">Download specific board voltage stability plot (3)\n"
                            "Choose a readback option: ")

    if TRCHOICE == "1":
        phase = Select_Phase()
        folder_path = os.path.join(DD, "DB_IMAGE",phase)
        try:
            os.makedirs(folder_path, exist_ok=True)
            Test_Results_Getter(folder_path, XLSX_NAME,phase)
            print(Fore.GREEN + "TEST DOWNLOAD COMPLETE")
            # now that this saves, lets give it a moment and then write all trace data, this may take some time
            time.sleep(0.2)
            Export_All_Traces(folder_path,phase)

        # just some generic error throws I stole that should be helpful
        except PermissionError:
            print("Error: No permission to write to this drive.")
        except OSError as e:
            print(f"Error creating folder or file: {e}")


    elif TRCHOICE == "2":
        #needs usb or other external mount at D
        drive_letter = "D"
        if os.path.exists(f"{drive_letter.upper()}:\\"):
            print(f"{drive_letter.upper()}: DRIVE FOUND")
            phase = Select_Phase()

            folder_path = os.path.join(f"{drive_letter.upper()}:\\", "DB_IMAGE",phase)

            try:
                #this is the actual writing setp, maybe I should prompt this for every n tests
                os.makedirs(folder_path, exist_ok=True)
                Test_Results_Getter(folder_path,XLSX_NAME,phase)
                print(Fore.GREEN + "TEST DOWNLOAD COMPLETE")
                #now that this saves, lets give it a moment and then write all trace data, this may take some time
                time.sleep(0.2)
                Export_All_Traces(folder_path,phase)

            #just some generic error throws I stole that should be helpful
            except PermissionError:
                print("Error: No permission to write to this drive.")
            except OSError as e:
                print(f"Error creating folder or file: {e}")
        else:
            print(f"{drive_letter.upper()}: DRIVE NOT FOUND.")

    elif TRCHOICE == "3":
        # specific board behavior plotting
        board_id = int(input("Board ID: "))
        phase = Select_Phase()
        if input("Warm or Cold Stability? (W/c)").lower() == "w":
            Voltage_Histogram(board_id,phase, [58.0, 61.0])
            sys.exit()
        Voltage_Histogram(board_id, phase, trace_column="multiple_power_cycle_voltage_c",
                          xrs=[48.0, 50.0], temp="(Cold)")

    elif TRCHOICE =="0":
        phasename = input("Input new phase name   ")
        add_phase(phasename)

    else:
        sys.exit("INVALID SELECTION")