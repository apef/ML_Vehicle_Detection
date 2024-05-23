import pyRTOS
from Obj_M5LoRaWANDriver import M5LoRaWAN868
from obj_object_detection import Detector
import cv2
import sys
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision

lora_device = None
detector = None


width = 640
height = 480
camera_id = 0
enable_edgetpu = False
num_threads = 4

model = "model/Webcam_Vehicle_ObjectDetection_model.tflite"
car, bus, bike, truck = 0,0,0,0

def prependIndx(val, indx):
    val = hex(val)
    return str(indx) + str(val)

def sendVehicleAmount(amountToSend):
    if (amountToSend > 0):
        lora_device.sendMSG(amountToSend)

def classificationAmounts(test):
    global car, truck, bus, bike
    while True:
        print("Amount of cars: {}, Trucks: {}, Buses: {}, Bikes: {}".format(car,truck,bus,bike))
        indexedCars = prependIndx(car, 1)
        indexedTrucks = prependIndx(truck, 2)
        indexedBus = prependIndx(bus, 3)
        indexedBike = prependIndx(bike, 4)
        
        if (car > 0 or truck > 0 or bus > 0 or bike > 0):
            lora_device.sendMSG(indexedCars)
            time.sleep(30)
            lora_device.sendMSG(indexedTrucks)
            time.sleep(30)
            lora_device.sendMSG(indexedBus)
            time.sleep(30)
            lora_device.sendMSG(indexedBike)
            
            car, truck, bus, bike = 0,0,0,0
            
        yield [pyRTOS.timeout(120)]

def lora_connection(test):
    global lora_device
      
    while True:
        print("still here, lora_connection")
        print("Lora Connection status:", lora_device.hasJoinedNetwork, lora_device.isconnected)
        yield [pyRTOS.timeout(60)]

def detection(task):
    global car, bus, bike, truck,width, height, camera_id, model, enable_edgetpu, num_threads    
    
    #image = None
    border_x = 300
    border_startY = 640
    border_stopY = 0
    border_color = (0,255,0)
    border_thickness = 3
    
    center_x, center_y = None,None
    
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    base_options = core.BaseOptions(file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
    detection_options = processor.DetectionOptions(max_results=3, score_threshold=0.3)
    options = vision.ObjectDetectorOptions(base_options=base_options, detection_options=detection_options)
  
    detector = vision.ObjectDetector.create_from_options(options)
    
    print("Detector successfully created")
    
    while cap.isOpened():
        
        success, image = cap.read()
        if not success:
          sys.exit('ERROR: Unable to open the camera')
          
       
        
        image = cv2.flip(image, 1)
        
    
        # The image is normally in Blue-Green_Red, which is different from the Red-Green-Blue
        # that tensorflow lite models use. Converting to the same color scheme.
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
        tensor_input_img = vision.TensorImage.create_from_array(rgb_image)
    
        
        detectionResult = detector.detect(tensor_input_img)
        
        for obj in detectionResult.detections:
            if obj is not None:
                #print(obj.categories[0].category_name)
                #print(obj.bounding_box.origin_x)
                
                
                # Get the X and Y values for where the bounding box is
                # draw from, as in, where there origins are in the pixels
                o_x = obj.bounding_box.origin_x
                o_y = obj.bounding_box.origin_y
                
                box_width = obj.bounding_box.width
                box_height = obj.bounding_box.height
                
                # Trying to find the center of the bounding box
                center_x = int(o_x + box_width/2)
                center_y = int(o_y + box_height/2)
                
                #print(center_x, center_y)
                
                # Count the detected object if it 'passes' the decision line
                # However due to the low fps of the video feed, the detected object
                # may not be on the line at a given frame. Thus making the check rather large
                # as such it counts an object if it is "close" to the line, not on it.
                if (center_x+10) > border_x and (center_x-10) < border_x:
                    classification = obj.categories[0].category_name
                    if classification == "Car":
                        car = car + 1
                    if classification == "Truck":
                        truck = truck + 1
                    if classification == "Bus":
                        bus = bus + 1
                    if classification == "Bike":
                        bike = bike + 1
        
        yield [pyRTOS.timeout(1)]

        
        # Wait 1ms to check if the user has pressed a key
        # This will then show the image created above for 1ms each loop
        # ensuring that the image output is shown in the imshow window
        #cv2.waitKey(1)
        
    cap.release()
    cv2.destroyAllWindows()
    

def main():
    global lora_device
    global detector
    port= "/dev/ttyS0"
    device_eui = "70B3D57ED0067783"
    app_eui = "0000000000000010"
    app_key = "0CB133ECDA9E4433A8869C515F86FC07"
    lora_device = M5LoRaWAN868(port, device_eui, app_eui, app_key)
    lora_device.run()
       
    while not (lora_device.hasJoinedNetwork):
        time.sleep(10)

    pyRTOS.add_task(pyRTOS.Task(detection, priority=1, name="color"))
    pyRTOS.add_task(pyRTOS.Task(classificationAmounts, priority=0, name="touch"))
    pyRTOS.add_task(pyRTOS.Task(lora_connection, priority=2, name="color"))
    

    pyRTOS.start()


main()
    
    
