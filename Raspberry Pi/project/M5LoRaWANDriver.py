import serial
import time
import threading

isconnected = False
device = None


def writeLoRa():
    
    while True:
        print("Writing..")
        device.write("AT+CGMI?\r\n".encode('utf-8'))
        time.sleep(1)


def readLoRa():
    while True:
        if device.in_waiting > 0:
            #print("Reading..")
            #device.write("AT+CGMI?\r\n")
        
            msg = device.readline().decode('utf-8').strip() 
            print(msg)
            #time.sleep(1)

def run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key):
    global device
    device = serial.Serial(port = port_,baudrate = 115200)

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
        
