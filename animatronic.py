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
    fps = max(1, min(fps, 15))
    frame_delay = 1.0 / fps
    msg = f"📡 Pi: Frame rate set to {fps:.1f} FPS ({frame_delay:.2f} s/frame)"
    socketio.emit('telemetry', msg)

@socketio.on('ping')
def handle_ping():
    socketio.emit('pong')

def camera_loop():
    frame_id = 0
    while True:
        try:
            image_stream = io.BytesIO()
            camera.capture_file(image_stream, format='jpeg')
            image_stream.seek(0)
            image_data = image_stream.read()
            socketio.emit('photo_data', image_data)
            socketio.emit('telemetry', f"📸 Pi: Frame #{frame_id} sent ({len(image_data)} bytes)")
            frame_id += 1
        except Exception as e:
            socketio.emit('telemetry', f"❌ Pi Error: {str(e)}")
        sleep(frame_delay)

if __name__ == '__main__':
    threading.Thread(target=camera_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
