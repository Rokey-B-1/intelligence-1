from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
from collections import Counter
import serial
import requests
from requests.auth import HTTPBasicAuth
import base64
import io
import threading

# Flask & SocketIO 초기화
app = Flask(__name__)
socketio = SocketIO(app)

ser = serial.Serial("/dev/ttyACM0", 9600)  # Arduino 연결

colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

api_url = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference"
ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"

is_running = False  # 프로세스 상태 플래그

def get_img():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Camera Error")
        exit(-1)
    ret, img = cam.read()
    cam.release()
    return img

def crop_img(img, size_dict):
    x = size_dict["x"]
    y = size_dict["y"]
    w = size_dict["width"]
    h = size_dict["height"]
    return img[y:y + h, x:x + w]

def inference_request(img):
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = io.BytesIO(img_encoded.tobytes())
    try:
        response = requests.post(
            api_url,
            auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
            headers={"Content-Type": "image/jpeg"},
            data=img_bytes.getvalue()
        )
        if response.status_code == 200:
            response_data = response.json()
            return response_data['objects']
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
    return []

def draw_detection_box(img, objects):
    class_counts = Counter([obj['class'] for obj in objects])
    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        if score < 0.7:
            continue
        x_min, y_min, x_max, y_max = obj['box']
        color = colors.get(class_name, (255, 255, 255))
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, 2)
        label = f"{class_name} ({score:.2f})"
        cv2.putText(img, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img

# WebSocket으로 클라이언트 요청 처리
@socketio.on('toggle_process')
def toggle_process():
    global is_running

    if is_running:
        # 프로세스를 중단
        is_running = False
        emit('process_status', {'status': 'stopped'})
        print("Process stopped.")
    else:
        # 프로세스를 시작
        is_running = True
        emit('process_status', {'status': 'running'})
        print("Process started.")
        thread = threading.Thread(target=process_image)
        thread.start()

def process_image():
    global is_running

    while is_running:
        data = ser.read()
        if data == b"0":
            img = get_img()
            crop_info = {"x": 270, "y": 100, "width": 300, "height": 300}
            if crop_info:
                img = crop_img(img, crop_info)
            objects = inference_request(img)
            img = draw_detection_box(img, objects)

            _, buffer = cv2.imencode('.jpg', img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            # WebSocket으로 이미지 전송
            socketio.emit('image_update', {'image': img_base64})
            ser.write(b"1")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
