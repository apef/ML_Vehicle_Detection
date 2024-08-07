import cv2
import sys
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import utils

width = 640
heigth = 480
camera_id = 0
enable_edgetpu = False
num_threads = 4

model_path = "Models_Webcam_NonCropped_ObjectDetection_V2_model-2348965855255068672_tflite_2024-05-14T07 41 48.523253Z_model.tflite"
car, bus, bike, truck = 0,0,0,0

class Detector():
    
    def __init__(self,_width, _height, _camera_id, _model, _enable_edgetpu, _num_threads):
        self.car,self.bus,self.bike,self.truck = 0,0,0,0
        self.width = _width
        self.height = _height
        self.camera_id = _camera_id
        self.model = _model
        self.enable_edgetpu = _enable_edgetpu
        self.num_threads = _num_threads
    
    
    def getVehicleAmount(self):
        tempC, tempT, tempBus, tempBike = self.car, self.truck, self.bus, self.bike
        self.car, self.truck, self.bus, self.bike = 0,0,0,0 # Reset the count after retrieval
        return tempC, tempT, tempBus, tempBike 
        
    def run(self):
        #global car, bus, bike, truck    
        
        #image = None
        border_x = 300
        border_startY = 640
        border_stopY = 0
        border_color = (0,255,0)
        border_thickness = 3
        
        center_x, center_y = None,None
        
        cap = cv2.VideoCapture(self.camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        base_options = core.BaseOptions(file_name=self.model, use_coral=self.enable_edgetpu, num_threads=self.num_threads)
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
                            self.car = self.car + 1
                        if classification == "Truck":
                            self.truck = self.truck + 1
                        if classification == "Bus":
                            self.bus = self.bus + 1
                        if classification == "Bike":
                            self.bike = self.bike + 1
                            
            image = utils.visualize(image, detectionResult)
            
            # The decision line
            cv2.line(image, (border_x, border_startY), (border_x, border_stopY), border_color, border_thickness)      
            
            if not center_x == None:
                # Center dot in bounding boxes
                cv2.circle(image, (center_x,center_y), 3, (0,255,0), 2)
            
            
            
            counts_txt = 'Cars: {}, Trucks: {}, Buses: {}, Bikes: {}'.format(self.car,self.truck,self.bus,self.bike)    
            cv2.putText(image, counts_txt, (20,20), cv2.FONT_HERSHEY_PLAIN,
                    1, (0,255,0), 2)
            
            #print(detectionResult)
            
            
            
            #cv2.imshow('object_detector', image)
            
            # Wait 1ms to check if the user has pressed a key
            # This will then show the image created above for 1ms each loop
            # ensuring that the image output is shown in the imshow window
            #cv2.waitKey(1)
            
        cap.release()
        cv2.destroyAllWindows()
