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
from PIL import Image
import io
import numpy as np
from time import sleep

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Initialize camera
camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
sleep(2)

@socketio.on('take_photo')
def handle_take_photo(data=None):
    print("Photo request received from desktop.")

    # Extract resolution scale from request
    scale_percent = 100
    if data and isinstance(data, dict):
        try:
            scale_percent = max(10, min(int(data.get('scale', 100)), 100))
        except Exception as e:
            print("Invalid scale value:", e)

    try:
        # Capture frame as RGB array
        frame = camera.capture_array("main")
        if frame is None:
            print("Failed to capture image.")
            return

        # Convert NumPy array to PIL image
        img = Image.fromarray(frame)

        # Resize if scale < 100%
        if scale_percent < 100:
            w, h = img.size
            new_size = (int(w * scale_percent / 100), int(h * scale_percent / 100))
            img = img.resize(new_size, Image.LANCZOS)

        # Encode image as JPEG in memory
        image_stream = io.BytesIO()
        img.convert("RGB").save(image_stream, format='JPEG')  # Always ensure RGB mode
        image_stream.seek(0)

        # Emit image
        socketio.emit('photo_data', image_stream.read())
        print(f"Sent photo at {scale_percent}% resolution.")

    except Exception as e:
        print("Error handling photo request:", e)

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000)
