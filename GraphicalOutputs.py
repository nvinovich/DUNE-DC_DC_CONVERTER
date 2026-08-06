import json
import os
from colorama import Fore
from FetchBoardData import get_connection
import matplotlib.pyplot as mp
import psycopg
import numpy as np

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
