import cv2
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

def main(width, height, camera_id, model, enable_edgetpu, num_threads):
    
    #image = None
    
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
        image = utils.visualize(image, detectionResult)
        
        print(detectionResult)
        cv2.imshow('object_detector', image)
        
    cap.release()
    cv2.destroyAllWindows()

main(width, heigth, camera_id, model_path, enable_edgetpu, num_threads)