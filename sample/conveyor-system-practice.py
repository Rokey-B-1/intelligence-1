import time
import serial
import requests
import numpy
import cv2
from io import BytesIO
from requests.auth import HTTPBasicAuth
from collections import Counter

ser = serial.Serial("/dev/ttyACM0", 9600) # connect with Arduino

# API endpoint
api_url = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference"
ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"

colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}


# Function - capture cam image
def get_img():
    """Get Image From USB Camera

    Returns:
        numpy.array: Image numpy array
    """

    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("Camera Error")
        exit(-1)

    ret, img = cam.read()
    cam.release()

    return img

# Function - crop the image
def crop_img(img, size_dict):
    x = size_dict["x"]
    y = size_dict["y"]
    w = size_dict["width"]
    h = size_dict["height"]
    img = img[y : y + h, x : x + w]
    
    return img

# Function - image inference (image preprocessing & inference)
def inference_reqeust(img: numpy.array, api_rul: str):
    """_summary_

    Args:
        img (numpy.array): Image numpy array
        api_rul (str): API URL. Inference Endpoint
    """
    _, img_encoded = cv2.imencode(".jpg", img)

    ### Prepare the image for sending ###
    img_bytes = BytesIO(img_encoded.tobytes())

    # Send the image to the API
    # files = {"file": ("image.jpg", img_bytes, "image/jpeg")}

    try:
        response = requests.post(
            url="https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference",
            auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
            headers={"Content-Type": "image/jpeg"},
            data=img_bytes,
        )   
        
        if response.status_code == 200:
            response_data = response.json()
            objects = response_data['objects']

            return objects
        
        else:
            print(f"Failed to send image. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
    
# Function - draw detection box on image
def draw_detection_box(img, objects) :
    image_cv = img
    class_counts = Counter([obj['class'] for obj in objects])
    
    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        if score < 0.7 :
            continue
        box = obj['box']  # [x_min, y_min, x_max, y_max]

        color = colors[class_name]
    
        x_min, y_min, x_max, y_max = box
        cv2.rectangle(image_cv, (x_min, y_min), (x_max, y_max), colors[class_name], 2)

        label = f"{class_name} ({score:.2f})"
        cv2.putText(image_cv, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_name], 2)
        

    y_offset = 30
    for i, (class_name, count) in enumerate(class_counts.items()):
        display_text = f"{class_name}: {count}"
        color = colors.get(class_name, (255, 255, 255))
        cv2.putText(image_cv, display_text, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
    return image_cv


while 1:
    data = ser.read()
    print(data)
    
    if data == b"0":
        img = get_img() # result of get_img func.
        # crop_info = None
        crop_info = {"x": 270, "y": 100, "width": 300, "height": 300}

        if crop_info is not None:
            img = crop_img(img, crop_info) # result of crop_img func.
            
        result = inference_reqeust(img, api_url) # result of inference_reqeust func.
        
        img = draw_detection_box(img, result)
            
        cv2.imshow("Raspberry PICO inspection", img)
        cv2.waitKey(1)

        ser.write(b"1")
        
    else:
        pass