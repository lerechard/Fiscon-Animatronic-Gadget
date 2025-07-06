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
base_config = camera.create_still_configuration()
base_size = base_config['size']  # Original resolution
camera.configure(base_config)
camera.start()
sleep(2)

@socketio.on('take_photo')
def handle_take_photo(data=None):
    print("Photo request received from desktop.")

    # Default to full resolution
    scale_percent = 100
    if data and isinstance(data, dict):
        try:
            scale_percent = max(10, min(int(data.get('scale', 100)), 100))
        except Exception as e:
            print("Invalid scale percent:", e)

    # Calculate scaled resolution
    new_width = int(base_size[0] * scale_percent / 100)
    new_height = int(base_size[1] * scale_percent / 100)

    # Configure camera for new size
    new_config = camera.create_still_configuration(size=(new_width, new_height))
    camera.configure(new_config)
    camera.start(show_preview=False)
    sleep(0.2)  # Let camera settle

    # Capture directly into memory
    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)

    socketio.emit('photo_data', image_stream.read())
    print(f"Photo sent at {new_width}x{new_height} resolution.")

    # Restore base config for next request
    camera.configure(base_config)
    camera.start(show_preview=False)
    sleep(0.2)
