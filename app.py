# app.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import subprocess
import sys
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# 다른 파이썬 파일을 실행한 프로세스를 저장할 변수
process = None

def start_other_script():
    """other_script.py 실행하여 이미지를 실시간으로 받아오는 함수"""
    global process
    if process is None:  # 다른 프로세스가 실행 중이지 않으면 실행
        process = subprocess.Popen([sys.executable, 'other_script.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        socketio.start_background_task(target=read_output)  # 이미지를 읽어오는 작업을 백그라운드에서 실행

def read_output():
    """실행 중인 프로세스의 stdout을 읽어서 실시간으로 클라이언트에 전송"""
    global process
    while True:
        output = process.stdout.readline()
        if output:
            base64_image = output.decode('utf-8').strip()  # 출력된 데이터를 문자열로 변환
            socketio.emit('new_image', {'image': base64_image})  # 클라이언트로 이미지 전송
        socketio.sleep(0.1)  # 0.1초 대기

def stop_other_script():
    """실행 중인 other_script.py 프로세스를 종료하는 함수"""
    global process
    if process:
        process.terminate()  # 프로세스를 종료
        process = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle_program', methods=['POST'])
def toggle_program():
    global process

    if process is None:
        # 프로그램이 실행되지 않은 상태 -> 실행
        start_other_script()  # 버튼 클릭 시 실행
        return jsonify(status='started')
    else:
        # 프로그램이 실행 중인 상태 -> 종료
        stop_other_script()  # 버튼 클릭 시 종료
        return jsonify(status='stopped')

if __name__ == '__main__':
    socketio.run(app, debug=True)
