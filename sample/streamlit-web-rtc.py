import streamlit as st
from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    WebRtcMode,
    RTCConfiguration,
)
import av
import cv2
from ultralytics import YOLO

# WebRTC 설정
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)


# YOLOv8 모델 로드
model = YOLO("yolov8n.pt")


# 비디오 프로세서 클래스 정의
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        # 모든 프레임에 대해 YOLO 추론
        results = model(img)

        # 예측 결과의 박스와 라벨을 영상에 표시
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                cls = box.cls[0]
                label = f"{model.names[int(cls)]} {conf:.2f}"

                # 사각형과 라벨을 이미지에 그리기 (글씨 크기 조절)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    img,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2,
                )  # 글씨 크기를 1.0으로 조절

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# 스트림릿 웹페이지
st.title("실시간 YOLOv8 추론 (웹캠 스트림 - 모든 프레임 추론)")

# WebRTC 스트리머
webrtc_ctx = webrtc_streamer(
    key="yolo-video-stream",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    video_processor_factory=VideoProcessor,
    async_processing=True,
)

st.write("웹캠 스트림을 통해 실시간으로 YOLOv8 추론 결과를 확인하세요.")
