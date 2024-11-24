from flask import Flask, render_template, Response
import threading
import serial
import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
from collections import Counter
from io import BytesIO
import time

app = Flask(__name__)

# Arduino 연결 설정
ser = serial.Serial("/dev/ttyACM0", 9600)

# API Endpoint 및 인증 정보
api_url = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference"
ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"

# 색상 정의
colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

# 글로벌 변수
latest_image = None  # 가장 마지막 처리된 이미지를 저장


# 카메라 이미지 캡처
def get_img():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise Exception("Camera Error")
    ret, img = cam.read()
    cam.release()
    return img


# 이미지 크롭
def crop_img(img, size_dict):
    x = size_dict["x"]
    y = size_dict["y"]
    w = size_dict["width"]
    h = size_dict["height"]
    return img[y:y + h, x:x + w]


# AI 추론 요청
def inference_request(img: np.array, api_url: str):
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = BytesIO(img_encoded.tobytes())
    try:
        response = requests.post(
            url=api_url,
            auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
            headers={"Content-Type": "image/jpeg"},
            data=img_bytes,
        )
        if response.status_code == 200:
            return response.json().get('objects', [])
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    return []


# 검출 결과 박스 그리기
def draw_detection_box(img, objects):
    class_counts = Counter([obj['class'] for obj in objects])
    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        if score < 0.7:
            continue
        x_min, y_min, x_max, y_max = obj['box']
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), colors[class_name], 2)
        label = f"{class_name} ({score:.2f})"
        cv2.putText(img, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_name], 2)
    return img


# 이벤트 루프 (스레드에서 실행)
def event_loop():
    global latest_image
    while True:
        data = ser.read()  # Arduino에서 신호 수신
        if data == b"0":
            img = get_img()
            crop_info = {"x": 270, "y": 100, "width": 300, "height": 300}
            if crop_info:
                img = crop_img(img, crop_info)
            result = inference_request(img, api_url)
            img = draw_detection_box(img, result)
            latest_image = img  # 글로벌 변수에 저장
            ser.write(b"1")  # 이벤트 트리거
        time.sleep(0.1)  # 루프 주기 설정


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/latest_image')
def get_latest_image():
    """가장 최근 처리된 이미지를 반환"""
    global latest_image
    if latest_image is not None:
        _, img_encoded = cv2.imencode('.jpg', latest_image)
        return Response(img_encoded.tobytes(), mimetype='image/jpeg')
    return "No image yet", 404


if __name__ == "__main__":
    # 이벤트 루프를 별도 스레드에서 실행
    thread = threading.Thread(target=event_loop, daemon=True)
    thread.start()
    app.run(debug=True)
