import serial
import time
import threading

isconnected = False
device = None



class TimerThread(threading.Thread):
    def __init__(self, timeout):
        super().__init__()
        self.timeout = timeout
        self.exception = None

    def run(self):
        startTime = time.time()
        while (time.time() - startTime < self.timeout):
            time.sleep(0.1)
        self.exception = TimeoutError("Time has run out, throwing exception to terminate executing code")        



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


# def timeDuration(startTime, timeout):
#     while True:
#         #print(time.time() - startTime, waitTime)
#         if (time.time() - startTime > timeout):
#             print("Time's up")
#             raise TimeoutError("Timeout reached")
    
def timer():
    print("Timer has been started")
    waitTime = 5
    startTime = time.time()
    
#     timerThread = threading.Thread(target=timeDuration(startTime, waitTime))
#     timerThread.start()
#     timerThread.join()
    timer_thread = TimerThread(waitTime)
    timer_thread.start()
# 
    timer_thread.join()
    if timer_thread.exception:
        raise timer_thread.exception

    

def sendCommand(command, waitTime):
    returnState = False
    response = ""
    startTime = time.time()
    
    #if (time.time() - startTime < waitTime):
    
    try:
      
        timer()
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
    except Exception as err:
        print("Command was not successfully sent")
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

