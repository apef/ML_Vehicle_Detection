import pyRTOS
from Obj_M5LoRaWANDriver import M5LoRaWAN868
from obj_object_detection import Detector


lora_device = None
detector = None

def classificationAmounts(test):
	while True:
		cars, trucks, buses, bikes = detector.getVehicleAmount()
		print("Amount of cars: {}, Trucks: {}, Buses: {}, Bikes: {}".format(cars,trucks,buses,bikes))
		yield [pyRTOS.timeout(120)]

def lora_connection(test):
    
      
	while True:
		print("Lora Connection status:", lora_device.hasJoinedNetwork)
		yield [pyRTOS.timeout(60)]

def createDetector(task):
    width = 640
    height = 480
    camera_id = 0
    enable_edgetpu = False
    num_threads = 4
    model_path = "Models_Webcam_NonCropped_ObjectDetection_V2_model-2348965855255068672_tflite_2024-05-14T07 41 48.523253Z_model.tflite"
    detector = Detector(width, height, camera_id, model_path, enable_edgetpu, num_threads)
    
    #lora_device.run()
    detector.run()
    

def main():
    global lora_device
    global detector
    port= "/dev/ttyS0"
    device_eui = "70B3D57ED0067783"
    app_eui = "0000000000000010"
    app_key = "0CB133ECDA9E4433A8869C515F86FC07"
    lora_device = M5LoRaWAN868(port, device_eui, app_eui, app_key)
    
   

#     model_path = "Models_Webcam_NonCropped_ObjectDetection_V2_model-2348965855255068672_tflite_2024-05-14T07 41 48.523253Z_model.tflite"
#     detector = Detector(width, height, camera_id, model_path, enable_edgetpu, num_threads)
#     
    lora_device.run()
#     detector.run()
    pyRTOS.add_task(pyRTOS.Task(createDetector, priority=1, name="color"))
    pyRTOS.add_task(pyRTOS.Task(task1, priority=0, name="touch"))
    pyRTOS.add_task(pyRTOS.Task(lora_connection, priority=2, name="color"))
    

    pyRTOS.start()


main()
    
    