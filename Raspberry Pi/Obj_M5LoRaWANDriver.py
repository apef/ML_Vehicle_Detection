import serial
import time
import threading
import multiprocessing
import re
import pyRTOS

class TimerThread(threading.Thread):
    def __init__(self, timeout):
        super().__init__()
        self.timeout = timeout
        self.exception = None

    def run(self):
        startTime = time.time()
        while (time.time() - startTime < self.timeout):
            time.sleep(1)
            #yield [pyRTOS.timeout(1)]
        #raise TimeoutError("Time's up")
        print("Timer Thread: Time's up")
        self.exception = TimeoutError("Time has run out, throwing exception to terminate executing code")        

class CommandResponse():
    def __init__(self):
        self.status = False
        self.msg = ""


class M5LoRaWAN868():
    def __init__(self, _port, _device_eui, _app_eui, _app_key):
        #print(arg)
        #self.port = _port
        print("Created loraobj")
        self.device_eui = _device_eui
        self.app_eui = _app_eui
        self.app_key = _app_key
        self.isconnected = False
        self.hasJoinedNetwork = False
        self.device = serial.Serial(port = _port,baudrate = 115200)
    

    def isModuleConnected(self):
        #global isconnected
        try:
            connectedStatus = self.sendCommand("AT+CGMI?\r\n", 3)
            print(connectedStatus.msg)
            if (connectedStatus.status):
                print("M5LoRaWAN868 Module is connected")
                self.isconnected = True
        finally:
            if not (self.isconnected):
                print("Failed to connect to M5LoRaWAN868 Module")
    
    
    def sendMSG(self, message):
        sendStr = "AT+DTRX=" + "{}".format(1) + "," + "{}".format(8) + "," + "{}".format(len(message)) + "," + message + "\r\n"
        #sendStr2 = "AT+DTRX=1,8,2,BB\r\n"
        response = self.sendCommand(sendStr, 10)
        
        if (response.status):
            print("Message successfully sent")
        else:
            print("Message was not able to be sent")
    
    def timer(waitTime):
        #print("Timer has been started")
        #waitTime = 5
        startTime = time.time()
        
        timer_thread = TimerThread(waitTime)
        timer_thread.start()

        timer_thread.join()
        if timer_thread.exception:
            raise timer_thread.exception
        
    def readSerial(self, response):
        #print("Read serials response:", response.status, response.msg)
        while True:
            
            #if device.in_waiting > 0:
                #print(time.time() - startTime)
                
            line = self.device.readline().decode('utf-8').strip()
            #print("line", line)
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
            #yield [pyRTOS.timeout(1)]
        
    def sendCommand(self, command, waitTime):
        returnState = False
        response = CommandResponse()
        responseStr = ""
        startTime = time.time()
        
        try:
            startTime = time.time()
        
            

            #timer(waitTime)
            print("Sending command", command)
            
            self.device.write(command.encode('utf-8'))
            
            #print("Starting to read")
            
            serRead_thread = multiprocessing.Process(target=self.readSerial(response))
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
                #yield [pyRTOS.timeout(1)]
            
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
        
    def joinNetwork(self):
        #global hasJoinedNetwork
        print("Trying to join network")
        command = "AT+CJOIN=1,0,60,8\r\n"
        if (self.sendCommand(command, 60)):
            print("JOINED NETWORK")
            self.hasJoinedNetwork = True
            
    def setup(self):
        currentDevEUI = self.sendCommand("AT+CDEVEUI?\r\n", 3)
        
        old_deveui = currentDevEUI.msg.split("\n")[2].replace("+CDEVEUI:","")
        
        if not (old_deveui == self.device_eui):
            print("Old deveui does not match, changing..")
            if (self.sendCommand("AT+CDEVEUI={}\r\n".format(device_eui),3)):
                print("Successfully changed Device EUI")
            else:
                print("Was unable to change Device EUI")
        else:
            print("Device EUI was already set")
    #         
        
        currentAPPEUI = self.sendCommand("AT+CAPPEUI?\r\n", 3)
        old_appeui = currentAPPEUI.msg.split("\n")[2].replace("+CDAPPEUI:","")
        
        if not (old_appeui == self.app_eui):
            print("Old appeui does not match, chaning..")
            if (self.sendCommand("AT+CAPPEUI={}\r\n".format(self.app_eui), 3)):
                print("Successfully changed App Eui")
            else:
                print("Was unable to change App Eui")
    #         
        
        currentAPPKEY = self.sendCommand("AT+CAPPKEY?\r\n", 3)
        old_appkey = currentAPPKEY.msg.split("\n")[2].replace("+CDAPPKEY:","")
        
        if not (old_appkey == self.app_key):
            print("Old appkey does not match, changing--")
            if (self.sendCommand("AT+CAPPKEY={}\r\n".format(self.app_key), 3)):
                print("Successfully changed Appkey")
            else:
                print("Was unable to change Appkey")
        else:
            print("APP key was already set")
            
        self.sendCommand("AT+CSAVE\r\n", 3)
    
    def run(self):
        print("Run")
        #self.device = 

        response = ""
        check = False 
        
        #checkT = threading.Thread(target=checkCodeExecutionStatus)
        #checkT.start()
        
        #print("Checking if Module is connected..")
        while not (self.isconnected):
            self.isModuleConnected()
    #     
        self.setup()
        
        print("Joining Network..")
        
        while not (self.hasJoinedNetwork):
            print("hasJoinedNetwork should be false", self.hasJoinedNetwork)
            self.joinNetwork()
            if self.hasJoinedNetwork:
                break
            #yield [pyRTOS.timeout(1)]
            time.sleep(30)
            
        
        #self.sendMSG("01C")
        #self.sendMSG("BB")
        #readThread = threading.Thread(target=readLoRa)
        #writeThread = threading.Thread(target=writeLoRa)
        
        
    #    try:
    #        response = 
        #readThread.start()
        
        print("End has been reached")
        
        
# 
# def main(port, device_eui, app_eui, app_key):
#     obj = M5LoRaWAN868(port, device_eui, app_eui, app_key)
#     
#     obj.run()
# 
# port= "/dev/ttyS0"
# device_eui = "70B3D57ED0067783"
# app_eui = "0000000000000010"
# app_key = "0CB133ECDA9E4433A8869C515F86FC07"

#main(port, device_eui, app_eui, app_key)