import os
import cv2
import socket
import threading
import time
import struct
import pyaudio
import RPi.GPIO as GPIO
import subprocess

# === AUTO INSTALL ===
os.system('pip install opencv-python pyaudio RPi.GPIO')

# === SETUP ===
CAMERA_ID = 0
DEST_PORT = 5000
AUDIO_PORT = 5001
CONTROL_PORT = 5002
HEARTBEAT_PORT = 5003

SERVO_PINS = {
    'U/D': 17,
    'L/R': 18,
    'Arms': 27,
    'Legs': 22,
    'Bonus': 23
}

GPIO.setmode(GPIO.BCM)
for pin in SERVO_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

servo_pwms = {k: GPIO.PWM(pin, 50) for k, pin in SERVO_PINS.items()}
for pwm in servo_pwms.values():
    pwm.start(7.5)

# === VIDEO STREAM ===
def video_stream():
    cap = cv2.VideoCapture(CAMERA_ID)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', DEST_PORT))
    sock.listen(1)
    conn, _ = sock.accept()
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        data = cv2.imencode('.jpg', frame)[1].tobytes()
        size = struct.pack('>L', len(data))
        conn.sendall(size + data)

# === AUDIO STREAM (MIC TO DESKTOP) ===
def audio_stream():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', AUDIO_PORT))
    sock.listen(1)
    conn, _ = sock.accept()

    while True:
        data = stream.read(CHUNK)
        conn.sendall(data)

# === RECEIVE CONTROL SIGNALS ===
def control_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', CONTROL_PORT))
    sock.listen(1)
    conn, _ = sock.accept()
    while True:
        data = conn.recv(1024)
        if not data:
            continue
        parts = data.decode().split(',')
        for i, key in enumerate(SERVO_PINS.keys()):
            val = float(parts[i])  # expected 0.0–1.0
            duty = 2.5 + 10 * val
            servo_pwms[key].ChangeDutyCycle(duty)

# === HEARTBEAT RESPONDER ===
def heartbeat():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', HEARTBEAT_PORT))
    while True:
        msg, addr = sock.recvfrom(1024)
        if msg == b'ping':
            sock.sendto(b'pong', addr)

# === MAIN ===
if __name__ == '__main__':
    print("Fiscon Animatronic Gadget started...")
    threading.Thread(target=video_stream).start()
    threading.Thread(target=audio_stream).start()
    threading.Thread(target=control_listener).start()
    threading.Thread(target=heartbeat).start()
