import psycopg
import os
from colorama import Fore

from Utilities import SELECT_PHASE
from WorkbookCreator import get_connection

extant_shipments = {
    "S1"
}

def Shipment_Board_Adder(board_id, phase, shipment):
    """
    allows imputation of a baord id ot a shipment.
    """
    with (get_connection() as conn):
        with conn.cursor() as cursor:
                #find this board
            cursor.execute(""" 
                        SELECT board_id
                        FROM dc_dc_tests
                        WHERE board_id = %s
                        AND phase = %s""",
                           (board_id,phase))
            if cursor.fetchone():
                cursor.execute("""
                                UPDATE dc_dc_tests
                                SET shipment = %s
                                WHERE board_id=%s
                                AND phase=%s
                            """, (shipment, board_id,phase))
                print(f"Added" + Fore.BLUE+f" {board_id}"," to shipment: "+Fore.BLUE +f"{shipment}")
                #if we cannot find it just skip and print that we could not find it
            else:
                print(Fore.RED + f"{board_id} not found in database")
            conn.commit()

def Shipment_Creator():
    #this just repeatedledy calls the above function on a
    print(Fore.MAGENTA+"\n                              Shipment Creator")

    phase = SELECT_PHASE()
    Sname = input(Fore.MAGENTA + "Input Shipment Name (see README for list of extant names): ")
    if Sname not in extant_shipments:
        #only allow my shipment names
        return

    ids = input(Fore.MAGENTA + "Please enter board ID's to include in the shipment. \n"
                         "Board ID's should be list with no leading or trailing spaces, such as "+'"012,014,110"\n')

    ids = ids.split(',')
    for id in ids:
        #tries to call on each, shouldn't throw any weird errors
        Shipment_Board_Adder(id,phase,Sname)
