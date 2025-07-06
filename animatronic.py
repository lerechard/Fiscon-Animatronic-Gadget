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

# Optional delay set by the desktop (0–1.0 seconds)
extra_delay = 0.0

@socketio.on('set_delay')
def set_delay(data):
    global extra_delay
    try:
        delay_val = float(data.get('delay', 0))
        extra_delay = max(0.0, min(delay_val, 1.0))
        socketio.emit('telemetry', f"📡 Pi: Delay set to {extra_delay:.2f} sec")
    except Exception as e:
        socketio.emit('telemetry', f"❌ Pi error setting delay: {e}")

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
            data = image_stream.read()
            socketio.emit('photo_data', data)
            socketio.emit('telemetry', f"📸 Pi: Frame {frame_id} sent ({len(data)} bytes)")
            frame_id += 1
        except Exception as e:
            socketio.emit('telemetry', f"❌ Pi error: {e}")
        sleep(extra_delay)

if __name__ == '__main__':
    threading.Thread(target=camera_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
