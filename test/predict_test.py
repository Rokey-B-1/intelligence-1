'''
API requests로 inference 정보를 받아와
클래스 별로 색깔이 다르게 detecting box 그리기
'''

import requests
from requests.auth import HTTPBasicAuth
import os
import cv2
import random
from collections import Counter

''' Variables '''
ACCESS_KEY = "B6wJEdHqC111qCcAKVnKR7rzHYz18sCJ2ig0y2JW"  # 보안

path = './test/test_img_v1.0'  # 이미지 파일들의 경로
save_path = './result_images'  # 결과 저장 경로
os.makedirs(save_path, exist_ok=True)

image_list = os.listdir(path)  # path of test image
random.shuffle(image_list)

# url_model_v1 = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2746c0ac-eec0-467b-a6da-a7308968fc16/inference"
url_model_v2 = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/2f719661-a7b7-4e33-9e0e-7a95676db182/inference"

defect_key = "defect"

colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

TP = []
FP = []

TN = []
FN = []

# 각 분류별 디렉토리 생성
for category in ['TP', 'FP', 'TN', 'FN']:
    os.makedirs(f"{save_path}/{category}", exist_ok=True)

for i, image in enumerate(image_list):
    img = f"{path}/{image}" # image path (real)
    img_binary = open(img, "rb").read() # image format for API send
    
    response = requests.post(
        url=url_model_v2,
        auth=HTTPBasicAuth("kdt2024_1-6", ACCESS_KEY),
        headers={"Content-Type": "image/jpeg"},
        data=img_binary,
    )
    
    response_data = response.json()  # response json data
    
    objects = [obj for obj in response_data['objects'] if obj['score'] >= 0.1]

    class_counts = Counter([obj['class'] for obj in objects]) # 각 클래스별로 개수 세기
    
    # 이미지 Load
    image_cv = cv2.imread(img, cv2.IMREAD_ANYCOLOR)
    
    
    ''' (최종 이미지 검수가 필요합니다!) '''
    ### 감지된 객체가 9개의 이미지 체크 / decision basis 1 ###
    if len(objects) == 9 :  
        ### 파츠가 제대로 검출 되었는지 / decision basis 2 ###
        if (class_counts.get('RASPBERRY PICO', 0) == 1 and
            class_counts.get('BOOTSEL', 0) == 1 and
            class_counts.get('CHIPSET', 0) == 1 and
            class_counts.get('USB', 0) == 1 and
            class_counts.get('OSCILLATOR', 0) == 1 and
            class_counts.get('HOLE', 0) == 4
        ) :
            TP.append(img)
            category = 'TP'
            
        else : 
            FP.append(img)
            category = 'FP'
    
    else :
        ### 이미지 파일명에 'defect'가 있는지  / decision basis 3 ### 
        if defect_key in img :
            TN.append(img)
            category = 'TN'
            
        else :
            FN.append(img)
            category = 'FN'
    
    
    ### detection 박스 그리기 ###        
    for obj in objects:
        class_name = obj['class']
        score = obj['score']
        box = obj['box']  # [x_min, y_min, x_max, y_max]

        color = colors[class_name]
        
        # 박스 그리기
        x_min, y_min, x_max, y_max = box
        cv2.rectangle(image_cv, (x_min, y_min), (x_max, y_max), colors[class_name], 2)

        # 텍스트 추가
        label = f"{class_name} ({score:.2f})"
        cv2.putText(image_cv, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_name], 2)
        
    # 왼쪽 위에 텍스트 쓰기
    y_offset = 30  # 텍스트 줄 간격
    for i, (class_name, count) in enumerate(class_counts.items()):
        display_text = f"{class_name}: {count}"
        color = colors.get(class_name, (255, 255, 255))  # 해당 클래스의 색상 사용
        cv2.putText(image_cv, display_text, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    """
    # 이미지 출력
    cv2.imshow("Raspberry PICO", image_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    """
    
    # 분류된 위치에 이미지 저장
    save_file_path = f"{save_path}/{category}/{image}"
    cv2.imwrite(save_file_path, image_cv)
    
# 리스트 저장
for category, data in zip(['TP', 'FP', 'TN', 'FN'], [TP, FP, TN, FN]):
    with open(f"{save_path}/{category}_list.txt", "w") as f:
        # 리스트 길이 저장
        f.write(f"Total {category} count: {len(data)}\n")
        f.write("="*30 + "\n")
        # 리스트 항목 저장
        for item in data:
            f.write(f"{item}\n")
