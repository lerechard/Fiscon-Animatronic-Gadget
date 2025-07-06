try:
    import flask
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'flask', 'flask-socketio', 'eventlet'])

try:
    from picamera2 import Picamera2
except ImportError:
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-picamera2'])
    exit("Re-run the script after installing Picamera2.")

from flask import Flask
from flask_socketio import SocketIO
import io
from time import sleep
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
sleep(2)

frame_delay = 1 / 5  # default: 5 FPS

@socketio.on('set_fps')
def set_fps(data):
    global frame_delay
    fps = data.get('fps', 5)
    frame_delay = 1.0 / max(0.1, min(fps, 15))
    print(f"Updated frame delay to {frame_delay:.2f} seconds per frame")

def camera_loop():
    while True:
        image_stream = io.BytesIO()
        camera.capture_file(image_stream, format='jpeg')
        image_stream.seek(0)
        socketio.emit('photo_data', image_stream.read())
        sleep(frame_delay)

if __name__ == '__main__':
    threading.Thread(target=camera_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
