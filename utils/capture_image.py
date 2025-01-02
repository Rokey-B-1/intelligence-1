""" 이미지를 캡쳐하는 프로그램입니다. """

import cv2
import os

save_directory = "img_capture"  # save directory is set to be under the current directory

def capture_image():
    os.makedirs(save_directory, exist_ok=True)

    file_prefix = input("Enter a file prefix to use : ")
    
    file_prefix = f'{file_prefix}_'
    print(file_prefix)
    
    image_count = 0
    # cap = cv2.VideoCapture(0)   # WebCam
    cap = cv2.VideoCapture(2)   # USB Camera
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    while True:
        ret, frame = cap.read()
        
        # resize 필요시
        # resized_frame = cv2.resize(frame, (640, 480))
        
        cv2.imshow("Webcam", frame)

        key = cv2.waitKey(1)
        if key == ord('c'):
            # 저장할 파일명 생성
            file_name = f'{save_directory}/{file_prefix}{image_count}.jpg'
            
            # 조정된 이미지를 저장
            cv2.imwrite(file_name, resized_frame)
            print(f"Image saved. name:{file_name}")
            image_count += 1
        
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    capture_image()

if __name__ == "__main__":
    main()
