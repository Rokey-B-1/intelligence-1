import cv2
import gradio as gr
import requests
import numpy as np
from PIL import Image
from requests.auth import HTTPBasicAuth
from collections import Counter

colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

# 가상의 비전 AI API URL (예: 객체 탐지 API)
VISION_API_URL = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference"
TEAM = "B-1"
ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"


def process_image(image):
    # 이미지를 OpenCV 형식으로 변환
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # 이미지를 API에 전송할 수 있는 형식으로 변환
    _, img_encoded = cv2.imencode(".jpg", image)

    # API 호출 및 결과 받기 - 실습1
    response = requests.post(
        VISION_API_URL,
        auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
        headers={"Content-Type": "image/jpeg"},
        data=img_encoded.tobytes(),
    )

    # API 결과를 바탕으로 박스 그리기 - 실습2
    response_data = response.json()  # response json 데이터
    objects = response_data.get('objects', [])  # 검출된 객체들 정보
    
    ### 검출된 객체 정보 카운트 ###
    class_counts = Counter([obj['class'] for obj in objects])
            
    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        box = obj['box']  # [x_min, y_min, x_max, y_max]

        color = colors[class_name]
        
        # 박스 그리기
        x_min, y_min, x_max, y_max = box
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)

        # 텍스트 추가
        label = f"{class_name} ({score:.2f})"
        cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
    # 왼쪽 위에 텍스트 쓰기
    y_offset = 30  # 텍스트 줄 간격
    for i, (class_name, count) in enumerate(class_counts.items()):
        display_text = f"{class_name}: {count}"
        color = colors.get(class_name, (255, 255, 255))  # 해당 클래스의 색상 사용
        cv2.putText(image, display_text, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)   
    
    
    # BGR 이미지를 RGB로 변환
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image)


# Gradio 인터페이스 설정
iface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(type="pil"),
    outputs="image",
    title="Vision AI Object Detection",
    description="Upload an image to detect objects using Vision AI.",
)

# 인터페이스 실행
iface.launch(share=True)
