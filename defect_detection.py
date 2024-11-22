from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import numpy as np
import serial
import requests
from io import BytesIO
from collections import Counter

# connect with Arduino
ser = serial.Serial("/dev/ttyACM0", 9600)

# Local server API url
api_url = "http://192.168.10.13:8881/inference/run"
params = {
    "min_confidence" : 0.7,
    "base_model" : "YOLOv6-L",
}

###
number_mapping = [None, "BOOTSEL", "CHIPSET", "HOLE", "OSCILLATOR", "RASPBERRY PICO", "USB"]
colors = {
    'RASPBERRY PICO': (25, 225, 138),
    'BOOTSEL': (0, 0, 255),
    'USB': (0, 136, 255),
    'CHIPSET': (62, 148, 16),
    'OSCILLATOR': (255, 8, 0),
    'HOLE': (255, 0, 225),
}

###
# Function - capture cam image
def get_img():
    """Get Image From USB Camera

    Returns:
        numpy.array: Image numpy array
    """

    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("Camera Error")
        exit(-1)

    ret, img = cam.read()
    cam.release()

    return 

# Function - crop the image
def crop_img(img, size_dict):
    x = size_dict["x"]
    y = size_dict["y"]
    w = size_dict["width"]
    h = size_dict["height"]
    img = img[y : y + h, x : x + w]
    
    return img

# Function - image inference (image preprocessing & inference)
def inference_reqeust(img: np.array, api_url: str):
    """_summary_

    Args:
        img (numpy.array): Image numpy array
        api_rul (str): API URL. Inference Endpoint
    """
    _, img_encoded = cv2.imencode(".jpg", img)

    ### Prepare the image for sending ###
    img_bytes = BytesIO(img_encoded.tobytes())

    # Send the image to the API
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
    
    try:
        response = requests.post(
            url=api_url,
            params=params,
            files=files
        )   
        
        if response.status_code == 200:
            response_data = response.json()
            objects = response_data['objects']
            
            print(objects)

            return objects
        
        else:
            print(f"Failed to send image. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        
# Function - draw detection box on image
def draw_detection_box(img, objects) :
    image_cv = img
    class_counts = Counter([number_mapping[obj['class_number']] for obj in objects])
    
    for obj in objects:
        class_name = number_mapping[obj['class_number']]
        score = obj['confidence']
        box = obj['bbox']  # [x_min, y_min, x_max, y_max]
        color = colors[class_name]
    
        box_int = [int(c) for c in box]
        x_min, y_min, x_max, y_max = box_int
        cv2.rectangle(image_cv, (x_min, y_min), (x_max, y_max), color, 2)

        label = f"{class_name} ({score:.2f})"
        cv2.putText(image_cv, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        

    y_offset = 10
    for i, (class_name, count) in enumerate(class_counts.items()):
        display_text = f"{class_name}: {count}"
        color = colors.get(class_name, (255, 255, 255))
        cv2.putText(image_cv, display_text, (10, y_offset + i * 13), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
    return image_cv
        
###

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1078, 673)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.StatusBox = QtWidgets.QLabel(self.centralwidget)
        self.StatusBox.setGeometry(QtCore.QRect(630, 50, 381, 81))
        self.StatusBox.setFrameShape(QtWidgets.QFrame.Panel)
        self.StatusBox.setLineWidth(2)
        self.StatusBox.setAlignment(QtCore.Qt.AlignCenter)
        self.StatusBox.setObjectName("StatusBox")
        self.ModeBtn = QtWidgets.QPushButton(self.centralwidget)
        self.ModeBtn.setGeometry(QtCore.QRect(60, 550, 240, 70))
        self.ModeBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.ModeBtn.setCheckable(False)
        self.ModeBtn.setChecked(False)
        self.ModeBtn.setObjectName("ModeBtn")
        self.ImageBox = QtWidgets.QLabel(self.centralwidget)
        self.ImageBox.setGeometry(QtCore.QRect(60, 40, 500, 500))
        self.ImageBox.setAutoFillBackground(False)
        self.ImageBox.setFrameShape(QtWidgets.QFrame.Box)
        self.ImageBox.setAlignment(QtCore.Qt.AlignCenter)
        self.ImageBox.setObjectName("ImagBox")
        self.RunBtn = QtWidgets.QPushButton(self.centralwidget)
        self.RunBtn.setEnabled(False)
        self.RunBtn.setGeometry(QtCore.QRect(320, 550, 240, 70))
        self.RunBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.RunBtn.setCheckable(False)
        self.RunBtn.setChecked(False)
        self.RunBtn.setObjectName("RunBtn")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(670, 530, 301, 71))
        self.pushButton_2.setObjectName("pushButton_2")
        self.DetectionInfoBox = QtWidgets.QLabel(self.centralwidget)
        self.DetectionInfoBox.setGeometry(QtCore.QRect(630, 150, 381, 351))
        self.DetectionInfoBox.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.DetectionInfoBox.setAlignment(QtCore.Qt.AlignCenter)
        self.DetectionInfoBox.setObjectName("DetectionInfoBox")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1078, 28))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        self.menu_3 = QtWidgets.QMenu(self.menubar)
        self.menu_3.setObjectName("menu_3")
        self.menu_4 = QtWidgets.QMenu(self.menubar)
        self.menu_4.setObjectName("menu_4")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action = QtWidgets.QAction(MainWindow)
        self.action.setObjectName("action")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menu_2.addAction(self.action)
        self.menu_3.addAction(self.actionExit)
        self.menu_4.addSeparator()
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_4.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menubar.addAction(self.menu_3.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        # Timer to update the image
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)  # Update every 100 ms

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.StatusBox.setText(_translate("MainWindow", "양품 / 불량"))
        self.ModeBtn.setText(_translate("MainWindow", "Auto"))
        self.ImagBox.setText(_translate("MainWindow", "Image is here!"))
        self.RunBtn.setText(_translate("MainWindow", "Next"))
        self.pushButton_2.setText(_translate("MainWindow", "Detection Log"))
        self.DetectionInfoBox.setText(_translate("MainWindow", "TextLabel"))
        self.menu.setTitle(_translate("MainWindow", "파일"))
        self.menu_2.setTitle(_translate("MainWindow", "로그"))
        self.menu_3.setTitle(_translate("MainWindow", "종료"))
        self.menu_4.setTitle(_translate("MainWindow", "시스템"))
        self.action.setText(_translate("MainWindow", "검수 로그"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))

    def update_image(self):
        data = ser.read()
        if data == b"0":
            img = get_img()
            crop_info = {"x": 270, "y": 100, "width": 300, "height": 300}

            if crop_info is not None:
                img = crop_img(img, crop_info)

            result = inference_reqeust(img, api_url)

            if result:
                img = draw_detection_box(img, result)

            # Convert the image to RGB format for displaying in QLabel
            rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.ImageBox.setPixmap(QPixmap.fromImage(q_image))

            ser.write(b"1")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
