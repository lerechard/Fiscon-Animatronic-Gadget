import os
import cv2
import socket
import threading
import struct
import pyaudio

os.system('pip install opencv-python pyaudio numpy')

VIDEO_PORT = 5000
AUDIO_PORT = 5001

def send_video():
    cap = cv2.VideoCapture(0)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', VIDEO_PORT))
    sock.listen(1)
    conn, _ = sock.accept()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        data = cv2.imencode('.jpg', frame)[1].tobytes()
        size = struct.pack('>L', len(data))
        conn.sendall(size + data)

def send_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', AUDIO_PORT))
    sock.listen(1)
    conn, _ = sock.accept()

    while True:
        data = stream.read(CHUNK)
        conn.sendall(data)

if __name__ == '__main__':
    threading.Thread(target=send_video).start()
    threading.Thread(target=send_audio).start()
