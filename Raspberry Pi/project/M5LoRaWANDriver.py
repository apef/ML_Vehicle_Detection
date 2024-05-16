import serial
import time
import threading
import multiprocessing
import re

isconnected = False
device = None
hasJoinedNetwork = False

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
        print("Timer Thread: Time's up")
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
    sendStr = "AT+DTRX=" + "{}".format(1) + "," + "{}".format(8) + "," + "{}".format(len(message)) + "," + message + "\r\n"
    #sendStr2 = "AT+DTRX=1,8,2,BB\r\n"
    response = sendCommand(sendStr, 10)
    
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
    print("Read serials response:", response.status, response.msg)
    while True:
        
        #if device.in_waiting > 0:
            #print(time.time() - startTime)
            
        line = device.readline().decode('utf-8').strip()
        print("line", line)
        response.msg = response.msg + line + "\n"
        #print(responseStr)
        if line == "OK":
            response.status = True
            #response.status = returnState
            break
        if line == "FAIL" or line == "+CME ERROR:1":
            response.status = False
            break
        if "ERR+" in line:
            response.status = False
            print("ERROR WAS FOUND")
            break
            
        time.sleep(0.5)
    #return response

def sendCommand(command, waitTime):
    returnState = False
    response = CommandResponse()
    responseStr = ""
    startTime = time.time()
    
    try:
        startTime = time.time()
    
        

        #timer(waitTime)
        print("Sending command", command)
        
        device.write(command.encode('utf-8'))
        
        print("Starting to read")
        
        serRead_thread = multiprocessing.Process(target=readSerial(response))
        serRead_thread.start()
        
        timer_thread = TimerThread(waitTime)
        timer_thread.start()
        #timer_thread.join()
       
        while (response.status == False):
            if timer_thread.exception:
                print("Time's up, terminating reading process")
                serRead_thread.terminate()
                serRead_thread.join()
                timer_thread.join()
                break
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
    global hasJoinedNetwork
    print("Trying to join network")
    command = "AT+CJOIN=1,0,60,8\r\n"
    if (sendCommand(command, 60)):
        print("JOINED NETWORK")
        hasJoinedNetwork = True
    
   
    

# "AT+CDEVEUI=" + device-eui + "\r\n"
# "AT+CAPPEUI=" + app_eui + "\r\n"
# 
# "AT+CAPPKEY=" + app_key + "\r\n"

def setup(device_eui, app_eui, app_key):
    currentDevEUI = sendCommand("AT+CDEVEUI?\r\n", 3)
    
    old_deveui = currentDevEUI.msg.split("\n")[2].replace("+CDEVEUI:","")
    
    if not (old_deveui == device_eui):
        print("Old deveui does not match, changing..")
        if (sendCommand("AT+CDEVEUI={}\r\n".format(device_eui),3)):
            print("Successfully changed Device EUI")
        else:
            print("Was unable to change Device EUI")
    else:
        print("Device EUI was already set")
#         
    
    currentAPPEUI = sendCommand("AT+CAPPEUI?\r\n", 3)
    old_appeui = currentAPPEUI.msg.split("\n")[2].replace("+CDAPPEUI:","")
    
    if not (old_appeui == app_eui):
        print("Old appeui does not match, chaning..")
        if (sendCommand("AT+CAPPEUI={}\r\n".format(app_eui), 3)):
            print("Successfully changed App Eui")
        else:
            print("Was unable to change App Eui")
#         
    
    currentAPPKEY = sendCommand("AT+CAPPKEY?\r\n", 3)
    old_appkey = currentAPPKEY.msg.split("\n")[2].replace("+CDAPPKEY:","")
    
    if not (old_appkey == app_key):
        print("Old appkey does not match, changing--")
        if (sendCommand("AT+CAPPKEY={}\r\n".format(app_key), 3)):
            print("Successfully changed Appkey")
        else:
            print("Was unable to change Appkey")
    else:
        print("APP key was already set")
        
    sendCommand("AT+CSAVE\r\n", 3)
    
    #deveuiSplit = deveuiSplit[2].replace("+CDEVEUI:","")
    #print(deveuiSplit)
#     matches = re.match(deveui_regex, currentDevEUI.msg)
#     oldDevEui = matches.group(0)
#     print(oldDevEui)
    
    

def run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key):
    global device
    device = serial.Serial(port = port_,baudrate = 115200)

    response = ""
    check = False 
    
    checkT = threading.Thread(target=checkCodeExecutionStatus)
    #checkT.start()
    
    print("Checking if Module is connected..")
    while not (isconnected):
        isModuleConnected()
#     
    setup(device_eui, app_eui, app_key)
    
    print("Joining Network..")
    
    while not (hasJoinedNetwork):
        print("hasJoinedNetwork should be false", hasJoinedNetwork)
        joinNetwork()
        if hasJoinedNetwork:
            break
        time.sleep(30)
    
    sendMSG("01C")
    sendMSG("BB")
    #readThread = threading.Thread(target=readLoRa)
    #writeThread = threading.Thread(target=writeLoRa)
    
    
#    try:
#        response = 
    #readThread.start()
    
    print("End has been reached")
    #writeThread.start()


port_= "/dev/ttyS0"
tx_pin = ""
rx_pin = ""
device_eui = "70B3D57ED0067783"
app_eui = "0000000000000010"
app_key = "0CB133ECDA9E4433A8869C515F86FC07"
run(port_, tx_pin, rx_pin, device_eui, app_eui, app_key)


