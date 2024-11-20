'''
API requests로 inference 정보를 받아와
클래스 별로 색깔이 다르게 detecting box 그리기
'''

import requests
from requests.auth import HTTPBasicAuth
import os
import cv2
from collections import Counter

ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"  # 보안

# Class별 색깔 지정
colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

path = './Raspberry_PICO_images'  # 이미지 파일들의 경로
image_list = os.listdir(path)  # 이미지 파일들의 파일명

for i, image in enumerate(image_list):
    img = f"{path}/{image}"
    img_binary = open(img, "rb").read()
    
    response = requests.post(
        url="https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference",
        auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
        headers={"Content-Type": "image/jpeg"},
        data=img_binary,
    )
    
    response_data = response.json()  # response json 데이터
    objects = response_data['objects'] # 검출된 객체들 정보

    ### 제대로 인식한 경우에만 출력 및 detection 박스 그리기 ###
    class_counts = Counter([obj['class'] for obj in objects])
    
    # Perfect 조건 체크
    if (
        class_counts.get('RASPBERRY PICO', 0) == 1 and
        class_counts.get('BOOTSEL', 0) == 1 and
        class_counts.get('CHIPSET', 0) == 1 and
        class_counts.get('USB', 0) == 1 and
        class_counts.get('OSCILLATOR', 0) == 1 and
        class_counts.get('HOLE', 0) == 4
    ):

        print(f"{i}번 이미지 입니다. - {img}")
        print(objects)
    
        # 이미지 Load
        image_cv = cv2.imread(img, cv2.IMREAD_ANYCOLOR)
            
        for obj in objects:
            class_name = obj['class']
            score = obj['score']
            box = obj['box']  # [x_min, y_min, x_max, y_max]

            color = colors[class_name]
            
            # 박스 그리기
            x_min, y_min, x_max, y_max = box
            cv2.rectangle(image_cv, (x_min, y_min), (x_max, y_max), color, 2)

            # 텍스트 추가
            label = f"{class_name} ({score:.2f})"
            cv2.putText(image_cv, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
        # 왼쪽 위에 텍스트 쓰기
        y_offset = 30  # 텍스트 줄 간격
        for i, (class_name, count) in enumerate(class_counts.items()):
            display_text = f"{class_name}: {count}"
            color = colors.get(class_name, (255, 255, 255))  # 해당 클래스의 색상 사용
            cv2.putText(image_cv, display_text, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # 이미지 출력
        cv2.imshow("Raspberry PICO", image_cv)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
