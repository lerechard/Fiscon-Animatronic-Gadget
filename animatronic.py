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

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
sleep(2)

@socketio.on('take_photo')
def handle_take_photo():
    try:
        image_stream = io.BytesIO()
        camera.capture_file(image_stream, format='jpeg')
        image_stream.seek(0)
        data = image_stream.read()
        socketio.emit('photo_data', data)
        socketio.emit('telemetry', f"📸 Pi: Photo taken and sent ({len(data)} bytes)")
    except Exception as e:
        socketio.emit('telemetry', f"❌ Pi error: {e}")

@socketio.on('ping')
def handle_ping():
    socketio.emit('pong')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
