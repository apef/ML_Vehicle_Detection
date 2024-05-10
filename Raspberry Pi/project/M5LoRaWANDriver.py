import serial
import time

isconnected = False
device = None


def run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key):
    device = serial.Serial(
        port = port_,
        baudrate = 115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    response = ""
    check = False 

#    try:
#        response = 

    while True:
        msg = device.readline()
        time.sleep(100)
        
