import serial
import time
import threading

isconnected = False
device = None


def isModuleConnected():
    global isconnected
    try:
        connectedStatus = sendCommand("AT+CGMI?\r\n", 3000)
        if (connectedStatus):
            print("M5LoRaWAN868 Module is connected")
            isconnected = True
    finally:
        if not (isconnected):
            print("Failed to connect to M5LoRaWAN868 Module")
    



def sendCommand(command, waitTime):
    returnState = False
    response = ""
    startTime = time.time()
    
    
    device.write(command.encode('utf-8'))
    while True:
        if (time.time() - startTime < waitTime):
            line = device.readline().decode('utf-8').strip()
            
            if line == "OK":
                returnState = True
                break
            if line == "FAIL":
                returnState = False
                break
        else:
            break
    return returnState
        

    


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
    
    print("Checking if Module is connected..")
    while not (isconnected):
        isModuleConnected()
    
    
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
        
