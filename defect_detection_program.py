import sys
import cv2
import numpy as np
import serial
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap

# Arduino Serial Communication
ser = serial.Serial("/dev/ttyACM0", 9600)

class ConveyorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.auto_mode = True  # Default mode is auto

    def initUI(self):
        # Layouts
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        # Camera Feed Label
        self.camera_label = QLabel(self)
        self.camera_label.setText("Camera Feed")
        self.camera_label.setFixedSize(640, 480)
        main_layout.addWidget(self.camera_label)

        # Manual/Auto Mode Button
        self.mode_button = QPushButton('Switch to Manual Mode', self)
        self.mode_button.clicked.connect(self.toggle_mode)
        button_layout.addWidget(self.mode_button)

        # Manual Control Button (Only enabled in Manual Mode)
        self.manual_control_button = QPushButton('Send Signal to Conveyor', self)
        self.manual_control_button.setEnabled(False)
        self.manual_control_button.clicked.connect(self.manual_control)
        button_layout.addWidget(self.manual_control_button)

        # Monitoring Text Box for OK/NG
        self.monitoring_text = QTextEdit(self)
        self.monitoring_text.setReadOnly(True)
        self.monitoring_text.setFixedHeight(50)
        self.monitoring_text.setPlaceholderText("OK/NG Status will be displayed here")
        main_layout.addWidget(self.monitoring_text)

        # YOLO Object Detection Info Text Box
        self.yolo_info_text = QTextEdit(self)
        self.yolo_info_text.setReadOnly(True)
        self.yolo_info_text.setFixedHeight(100)
        self.yolo_info_text.setPlaceholderText("YOLO Object Detection Info will be displayed here")
        main_layout.addWidget(self.yolo_info_text)

        # Dummy Log Button
        self.log_button = QPushButton('View Logs (Dummy)', self)
        button_layout.addWidget(self.log_button)

        # Set Layouts
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Set Window Title
        self.setWindowTitle('Conveyor Belt Control and Monitoring System')
        self.setGeometry(100, 100, 800, 600)

        # Start Timer for Automatic Camera Update
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

    def toggle_mode(self):
        if self.auto_mode:
            self.auto_mode = False
            self.mode_button.setText('Switch to Auto Mode')
            self.manual_control_button.setEnabled(True)
        else:
            self.auto_mode = True
            self.mode_button.setText('Switch to Manual Mode')
            self.manual_control_button.setEnabled(False)

    def manual_control(self):
        if not self.auto_mode:
            # Send signal to Arduino to control conveyor belt manually
            ser.write(b'1')

    def update_frame(self):
        # Capture frame-by-frame
        ret, frame = self.get_img()
        if ret:
            # Convert image to RGB format
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, QtCore.Qt.KeepAspectRatio)
            self.camera_label.setPixmap(QPixmap.fromImage(p))

            # Placeholder for YOLO object detection (Dummy Text)
            self.yolo_info_text.setText("Detected Objects: RASPBERRY PICO, USB, OSCILLATOR")

            # Placeholder for OK/NG status (Dummy Text)
            self.monitoring_text.setText("Status: OK")

    def get_img(self):
        # Simulate capturing an image from USB Camera
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            print("Camera Error")
            return False, None

        ret, img = cam.read()
        cam.release()
        return ret, img

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = ConveyorApp()
    ex.show()
    sys.exit(app.exec_())
