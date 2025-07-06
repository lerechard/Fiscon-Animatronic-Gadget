# animatronic.py (Fiscon animatronic gadget)

DESKTOP_IP = '100.65.32.9'  # <-- your desktop IP

from flask import Flask, Response
from flask_socketio import SocketIO
import cv2
import threading
import pyaudio
import socket
import io
import wave
from gpiozero import Servo
from time import sleep

# Init servos
servo_ud = Servo(17)
servo_lr = Servo(27)
servo1 = Servo(22)
servo2 = Servo(5)
servo3 = Servo(6)

# Init Flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Camera stream
camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        if not camera.isOpened():
            print("Camera not available.")
            sleep(1)
            continue

        success, frame = camera.read()
        if not success:
            print("Failed to read frame.")
            continue

        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Audio stream (mic → desktop)
def stream_mic():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)

    while True:
        try:
            s = socket.socket()
            s.connect((DESKTOP_IP, 9002))
            print("Connected to desktop for mic stream.")
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                s.sendall(data)
        except Exception as e:
            print("Audio stream error:", e)
            sleep(2)  # retry after delay
        finally:
            s.close()

# Audio playback (desktop → speaker)
@socketio.on('audio_chunk')
def handle_audio(data):
    try:
        audio = wave.open(io.BytesIO(data), 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio.getsampwidth()),
                        channels=audio.getnchannels(),
                        rate=audio.getframerate(),
                        output=True)
        chunk = audio.readframes(1024)
        while chunk:
            stream.write(chunk)
            chunk = audio.readframes(1024)
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print("Audio playback error:", e)

# Clamp servo values
def clamp(value):
    return max(-1.0, min(1.0, float(value)))

# Servo control
@socketio.on('servo_control')
def servo_control(data):
    try:
        servo_ud.value = clamp(data['ud'])
        servo_lr.value = clamp(data['lr'])
        servo1.value = clamp(data['s1'])
        servo2.value = clamp(data['s2'])
        servo3.value = clamp(data['s3'])
    except Exception as e:
        print("Servo control error:", e)

if __name__ == '__main__':
    threading.Thread(target=stream_mic, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
