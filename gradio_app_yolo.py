import cv2
import gradio as gr
import numpy as np
from PIL import Image
from ultralytics import YOLO

# YOLOv8 모델 로드
yolo_model = YOLO("yolov8n.pt")

def process_image(image):
    """
    이미지 처리 함수: YOLOv8 모델로 객체 감지를 수행.
    """
    image_np = np.array(image)
    
    # YOLOv8 모델로 감지 수행
    results = yolo_model(image_np)

    result_image = Image.fromarray(results[0].plot())
    
    return result_image

# Gradio 인터페이스 설정
iface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(type="pil"),
    outputs="image",
    title="Vision AI Object Detection (with YOLOv8)",
    description="Upload an image to detect objects using Vision AI.",
)

# 인터페이스 실행
iface.launch()
