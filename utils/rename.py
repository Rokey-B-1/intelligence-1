""" 테스트 이미지 수집시에 파일의 이름을 변경하는 프로그램입니다. """

import os
import random

def rename_images_randomly(folder_path):
    # 폴더 내 모든 파일 목록 가져오기
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # 이미지 파일만 필터링 (jpg, png 등 확장자 추가 가능)
    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
    
    # 파일 목록 랜덤하게 섞기
    random.shuffle(image_files)
    
    # 파일명 변경
    for i, file_name in enumerate(image_files):
        # 원래 파일 경로
        old_path = os.path.join(folder_path, file_name)
        
        # 새로운 파일명과 경로 생성
        new_name = f"{i}.jpg"  # 확장자는 원래 파일과 동일하게 설정 가능
        new_path = os.path.join(folder_path, new_name)
        
        # 파일 이름 변경
        os.rename(old_path, new_path)
        print(f"Renamed: {file_name} -> {new_name}")

# 사용 예제
folder_path = "./img_capture"  # 이미지가 있는 폴더 경로 / 사용 환경에 따라 변경 필요 
rename_images_randomly(folder_path)
