try:
    import flask
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'flask', 'flask-socketio', 'eventlet'])

try:
    import pyaudio
    import numpy
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'pyaudio', 'numpy'])

try:
    from picamera2 import Picamera2
except ImportError:
    import subprocess
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-picamera2'])
    exit("Re-run the script after installing Picamera2.")

from flask import Flask, request
from flask_socketio import SocketIO, emit
import io
import threading
import time
import pyaudio

# Flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Base resolution
BASE_WIDTH = 640
BASE_HEIGHT = 480

# Initialize camera
camera = Picamera2()
current_resolution = (BASE_WIDTH, BASE_HEIGHT)
camera.configure(camera.create_still_configuration(main={"size": current_resolution}))
camera.start()
time.sleep(2)

# Audio setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio_interface = pyaudio.PyAudio()

# Playback stream (from desktop)
playback_stream = audio_interface.open(format=FORMAT,
                                       channels=CHANNELS,
                                       rate=RATE,
                                       output=True,
                                       frames_per_buffer=CHUNK)

# Recording stream (to desktop)
recording_stream = audio_interface.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK)

audio_clients = set()
stream_audio = True

@socketio.on('take_photo')
def handle_take_photo():
    client_sid = request.sid
    print(f"Photo request received from {client_sid}")

    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)
    image_bytes = image_stream.read()

    socketio.emit('photo_data', image_bytes, room=client_sid)
    print(f"Photo sent to {client_sid}")

@socketio.on('set_resolution')
def handle_set_resolution(scale):
    global current_resolution, camera
    try:
        scale = float(scale)
        width = max(160, int(BASE_WIDTH * scale))    # Enforce a safe minimum
        height = max(120, int(BASE_HEIGHT * scale))
        new_resolution = (width, height)
        print(f"Setting new resolution: {new_resolution}")

        camera.stop()
        camera.configure(camera.create_still_configuration(main={"size": new_resolution}))
        camera.start()
        current_resolution = new_resolution
    except Exception as e:
        print("Failed to set resolution:", e)

@socketio.on('connect')
def handle_connect():
    client_sid = request.sid
    print(f"Client connected: {client_sid}")
    audio_clients.add(client_sid)

@socketio.on('disconnect')
def handle_disconnect():
    client_sid = request.sid
    print(f"Client disconnected: {client_sid}")
    audio_clients.discard(client_sid)

@socketio.on('audio_chunk_to_pi')
def handle_audio_chunk(data):
    playback_stream.write(data)

def stream_audio_to_clients():
    while stream_audio:
        try:
            data = recording_stream.read(CHUNK, exception_on_overflow=False)
            for sid in list(audio_clients):
                socketio.emit('audio_chunk_from_pi', data, room=sid)
        except Exception as e:
            print("Error streaming audio:", e)
        time.sleep(0.001)

# Start audio streaming in background thread
audio_thread = threading.Thread(target=stream_audio_to_clients, daemon=True)
audio_thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
