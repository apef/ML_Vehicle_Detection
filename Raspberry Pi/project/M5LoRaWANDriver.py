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
    
def sendMSG(message):
    sendStr = "AT+DTRX=" + "{}".format(1) + "{}".format(3) + "{}".format(len(message)) + message + "\r\n"
    
    response = sendCommand(message, 5000)
    
    if (response):
        print("Message successfully sent")
    else:
        print("Message was not able to be sent")

def timer():
    print("Timer has been started")
    waitTime = 5
    startTime = time.time()
    
    while True:
        #print(time.time() - startTime, waitTime)
        if (time.time() - startTime > waitTime):
            print("Time's up")
            raise ValueError('Time has run out, throwing exception to terminate executing code')

def sendCommand(command, waitTime):
    returnState = False
    response = ""
    startTime = time.time()
    
    #if (time.time() - startTime < waitTime):
    
    try:
        timerThread = threading.Thread(target=timer)
        timerThread.start()
        
        print("Sending command")
        device.write(command.encode('utf-8'))
        
        print("Starting to read")
        while True:
            #print(time.time() - startTime)
        
            line = device.readline().decode('utf-8').strip()
            
            if line == "OK":
                returnState = True
                break
            if line == "FAIL":
                returnState = False
                break
    except ValueError as err:
        print(err.args, "Command was not successfully sent")
    finally:
        return returnState
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

def checkCodeExecutionStatus():
    print("Checking if code is still executing")
    while True:
        print("Still executing")
        time.sleep(2)

def run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key):
    global device
    device = serial.Serial(port = port_,baudrate = 115200)

    response = ""
    check = False 
    
    checkT = threading.Thread(target=checkCodeExecutionStatus)
    checkT.start()
    
    print("Checking if Module is connected..")
    while not (isconnected):
        isModuleConnected()
    
    
    print("Starting threads..")
    sendMSG("Test")
    #readThread = threading.Thread(target=readLoRa)
    #writeThread = threading.Thread(target=writeLoRa)
    
    
#    try:
#        response = 
    #readThread.start()
    #writeThread.start()


port_= "/dev/ttyS0"
tx_pin = ""
rx_pin = ""
device_eui = ""
app_eui = ""
app_key = ""
run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key)
        
