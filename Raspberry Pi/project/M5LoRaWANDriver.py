import serial
import time
import threading

isconnected = False
device = None


def writeLoRa():
    print("Writing..")
    while True:
        device.write("AT+CGMI?\r\n".encode('utf-8'))
        time.sleep(1000)


def readLoRa():
    while True:
        print("Reading..")
        #device.write("AT+CGMI?\r\n")
        
        msg = device.readline()
        
        time.sleep(1000)

def run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key):
    global device
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
    
    print("Starting threads..")
    readThread = threading.Thread(target=readLoRa)
    writeThread = threading.Thread(target=writeLoRa)
#    try:
#        response = 
    readThread.start()
    writeThread.start()

port_= "/dev/ttyS0"
tx_pin = ""
rx_pin = ""
device_eui = ""
app_eui = ""
app_key = ""
run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key)
        
