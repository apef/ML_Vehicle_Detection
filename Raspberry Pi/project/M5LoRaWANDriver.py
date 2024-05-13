import serial
import time
import threading
import multiprocessing

isconnected = False
device = None


class CommandResponse():
    def __init__(self):
        self.status = False
        self.msg = ""
    

class TimerThread(threading.Thread):
    def __init__(self, timeout):
        super().__init__()
        self.timeout = timeout
        self.exception = None

    def run(self):
        startTime = time.time()
        while (time.time() - startTime < self.timeout):
            time.sleep(1)
        #raise TimeoutError("Time's up")
        self.exception = TimeoutError("Time has run out, throwing exception to terminate executing code")        



def isModuleConnected():
    global isconnected
    try:
        connectedStatus = sendCommand("AT+CGMI?\r\n", 3)
        print(connectedStatus.msg)
        if (connectedStatus.status):
            print("M5LoRaWAN868 Module is connected")
            isconnected = True
    finally:
        if not (isconnected):
            print("Failed to connect to M5LoRaWAN868 Module")
    
def sendMSG(message):
    sendStr = "AT+DTRX=" + "{}".format(1) + "{}".format(3) + "{}".format(len(message)) + message + "\r\n"
    
    response = sendCommand(message, 10)
    
    if (response.status):
        print("Message successfully sent")
    else:
        print("Message was not able to be sent")

    
def timer(waitTime):
    print("Timer has been started")
    #waitTime = 5
    startTime = time.time()
    
    timer_thread = TimerThread(waitTime)
    timer_thread.start()

    timer_thread.join()
    if timer_thread.exception:
        raise timer_thread.exception

def readSerial(response):
    while True:
        
        if device.in_waiting > 0:
            #print(time.time() - startTime)
            
            line = device.readline().decode('utf-8').strip()
            print("line", line)
            response.msg = response.msg + line
            #print(responseStr)
            if line == "OK":
                response.status = True
                #response.status = returnState
                break
            if line == "FAIL":
                response.status = False
                break
    #return response

def sendCommand(command, waitTime):
    returnState = False
    response = CommandResponse()
    responseStr = ""
    startTime = time.time()
    
    try:
        startTime = time.time()
    
        timer_thread = TimerThread(waitTime)
        timer_thread.start()

      
        #timer(waitTime)
        print("Sending command")
        device.write(command.encode('utf-8'))
        
        print("Starting to read")
        
        serRead_thread = multiprocessing.Process(target=readSerial(response))
        serRead_thread.start()
        
        timer_thread.join()
        
        
        while (response.status == False):
            if timer_thread.exception:
                print("Time's up, terminating reading process")
                serRead_thread.terminate()
                serRead_thread.join()
            time.sleep(0.5)
        
        print("The response status is: ", response.status)
        print("The response msg is: ", response.msg)
#         while True:
#             if device.in_waiting > 0:
#             #print(time.time() - startTime)
#             
#                 line = device.readline().decode('utf-8').strip()
#                 print("line", line)
#                 responseStr = responseStr + line
#                 print(responseStr)
#                 if line == "OK":
#                     returnState = True
#                 #response.status = returnState
#                     break
#                 if line == "FAIL":
#                     returnState = False
#                     break
            
    except Exception as err:
        print(err.args, "Command was not successfully sent")
    finally:
#         response.status = returnState
#         response.msg = responseStr
        #print("This executed")
        return response
    #return returnState
        

    


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
        
def joinNetwork():
    command = "AT+CJOIN=1,0,60,8\r\n"
    sendCommand(command, 10)
    
    print("Trying to join network")
    

#def setup(device_eui, app_eui, app_key):
    

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
    
    #setup()
    
    #print("Joining Network..")
    #joinNetwork()
    #sendMSG("Test")
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

