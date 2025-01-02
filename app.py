""" 클라우드 엔드포인트에서 추론값을 가져오는 통합 프로그램입니다. """

from flask import Flask, render_template, Response, jsonify, request, url_for
import threading
import serial
import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
from collections import Counter
from io import BytesIO
import time
import os
import sqlite3
import secrets
import string

app = Flask(__name__)

# 글로벌 변수
latest_image = None  # 가장 마지막 처리된 이미지를 저장
latest_prediction = None  # 가장 최근 판단 결과
latest_product_code = None  # 가장 최근 제품 코드
latest_class_counts = None # 가장 최근 제품의 YOLO 인식 결과

# 데이터베이스 경로
db_path = "products.db"

# 저장 경로 설정
save_path = os.path.join('static', 'images')
os.makedirs(save_path, exist_ok=True)

# Arduino 연결 설정
ser = serial.Serial("/dev/ttyACM0", 9600)

# API Endpoint 및 인증 정보
api_url = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/83811d26-5705-4173-9406-b963ceb915c3/inference"
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

# Pass/Fail 기준
standard = {
    "BOOTSEL": 1,
    "USB": 1,
    "CHIPSET": 1,
    "OSCILLATOR": 1,
    "RASPBERRY PICO": 1,
    "HOLE": 4
}


def initialize_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 제품검수 (
            PRODUCT_NUM TEXT PRIMARY KEY,
            BOOTSEL INTEGER NOT NULL,
            USB INTEGER NOT NULL,
            CHIPSET INTEGER NOT NULL,
            OSCILLATOR INTEGER NOT NULL,
            RASPBERRY_PICO INTEGER NOT NULL,
            HOLE INTEGER NOT NULL,
            PREDICT TEXT NOT NULL,
            ACTUAL TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
def generate_product_code(length=8):
    """안전한 제품 코드 생성"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_to_database(product_code, class_counts, prediction, image):
    """데이터베이스와 이미지 저장"""
    # 이미지 저장
    img_filename = f"{save_path}/{product_code}.jpg"
    cv2.imwrite(img_filename, image)
    
    # DB 저장
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO 제품검수 (
            PRODUCT_NUM, BOOTSEL, USB, CHIPSET, OSCILLATOR,
            RASPBERRY_PICO, HOLE, PREDICT, ACTUAL
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ( 
        product_code,
        class_counts.get("BOOTSEL", 0),
        class_counts.get("USB", 0),
        class_counts.get("CHIPSET", 0),
        class_counts.get("OSCILLATOR", 0),
        class_counts.get("RASPBERRY PICO", 0),
        class_counts.get("HOLE", 0),
        prediction,
        None
    ))
    conn.commit()
    conn.close()

def async_save_to_database(product_code, class_counts, prediction, img):
    """데이터베이스 저장 작업을 별도 스레드에서 실행"""
    thread = threading.Thread(target=save_to_database, args=(product_code, class_counts, prediction, img))
    thread.start()

# 카메라 이미지 캡처
def get_img():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise Exception("Camera Error")
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


def draw_detection_box(img, objects):
    global latest_prediction, latest_product_code, latest_class_counts

    class_counts = Counter([obj['class'] for obj in objects])
    latest_class_counts = dict(class_counts)  # 클래스 카운트를 글로벌 변수로 저장

    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        if score < 0.7:
            continue
        x_min, y_min, x_max, y_max = obj['box']
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), colors[class_name], 2)
        label = f"{class_name} ({score:.2f})"
        cv2.putText(img, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_name], 2)

    # Pass/Fail 판단
    is_pass = all(class_counts.get(part, 0) == count for part, count in standard.items())
    prediction = "Pass" if is_pass else "Fail"
    product_code = generate_product_code()

    # 최신 판단 결과 업데이트
    latest_prediction = prediction
    latest_product_code = product_code

    # DB에 비동기로 저장
    async_save_to_database(product_code, class_counts, prediction, img)

    return img

# 이벤트 루프
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
        time.sleep(0.2)
        
        
##################################################################################

# 메인 페이지 라우터
@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

# 검수 페이지 라우터
@app.route('/inspection')
def inspection():
    """데이터베이스에서 데이터 불러와 보여주는 페이지"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM 제품검수")
    data = cursor.fetchall()
    conn.close()
    return render_template('inspection.html', data=data)


# 검수 페이지에서 실제 양품 / 불량 체크 라우터
@app.route('/update_actual', methods=['POST'])
def update_actual():
    """ACTUAL 열 업데이트"""
    product_num = request.form.get("product_num")
    actual_status = request.form.get("actual_status")
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE 제품검수 SET ACTUAL = ? WHERE PRODUCT_NUM = ?", (actual_status, product_num))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "product_num": product_num, "actual_status": actual_status})

# 검수 페이지에서 이미지 불러오는 라우터
@app.route('/get_image/<product_num>')
def get_image(product_num):
    """해당 PRODUCT_NUM의 이미지를 반환"""
    image_path = os.path.join(save_path, f"{product_num}.jpg")  # static/Images 기준 경로
    if os.path.exists(image_path):
        return jsonify({"image_url": f"/static/images/{product_num}.jpg"})  # URL 경로 반환
    else:
        return jsonify({"error": "Image not found"}), 404

    
# 통계 페이지 라우터
@app.route('/statistics')
def statistics():
    """통계 페이지"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 검수 완료와 미완료 개수
    cursor.execute("SELECT COUNT(*) FROM 제품검수 WHERE ACTUAL IS NOT NULL")
    completed_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM 제품검수 WHERE ACTUAL IS NULL")
    pending_count = cursor.fetchone()[0]
    
    # TP, FP, FN, TN 계산
    cursor.execute("SELECT PREDICT, ACTUAL FROM 제품검수 WHERE ACTUAL IS NOT NULL")
    results = cursor.fetchall()
    
    tp = sum(1 for pred, actual in results if pred == "Pass" and actual == "Pass")
    fp = sum(1 for pred, actual in results if pred == "Pass" and actual == "Fail")
    fn = sum(1 for pred, actual in results if pred == "Fail" and actual == "Pass")
    tn = sum(1 for pred, actual in results if pred == "Fail" and actual == "Fail")
    
    # Precision, Recall 계산
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    conn.close()
    
    return render_template('statistics.html', 
                           completed_count=completed_count, 
                           pending_count=pending_count,
                           tp=tp, fp=fp, fn=fn, tn=tn,
                           precision=precision, recall=recall)


@app.route('/latest_image')
def get_latest_image():
    """가장 최근 처리된 이미지를 반환"""
    global latest_image, latest_prediction, latest_product_code, latest_class_counts

    if latest_image is not None:
        _, img_encoded = cv2.imencode('.jpg', latest_image)
        return jsonify({
            "image": img_encoded.tobytes().hex(),  # 이미지 데이터를 Hex로 변환
            "prediction": latest_prediction,
            "product_code": latest_product_code,
            "class_counts": latest_class_counts  # 클래스 카운트 추가
        })
    return "No image yet", 404


if __name__ == "__main__":
    initialize_database()
    thread = threading.Thread(target=event_loop, daemon=True)
    thread.start()
    app.run(debug=True)


