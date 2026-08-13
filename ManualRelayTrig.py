import time
import Utilities

RELAY = Utilities.SERIAL_CONNECTOR()
running = True
print("RELAY CONTROL\n] for 200 ms pulse, other to quit: ")

while running:

    if input("") == ("]"):
        RELAY.write(b"relay on 000\r")
        time.sleep(0.5)
        RELAY.write(b"relay off 000\r")

    else: running = False