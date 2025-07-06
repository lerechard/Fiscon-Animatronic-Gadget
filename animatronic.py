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

    # Default scale is 100% (no resize)
    scale_percent = 100
    if data and isinstance(data, dict):
        try:
            scale_percent = max(10, min(int(data.get('scale', 100)), 100))
        except Exception as e:
            print("Invalid scale value received:", e)

    # Capture raw image
    frame = camera.capture_array()
    img = Image.fromarray(frame)

    # Resize image if needed
    if scale_percent < 100:
        w, h = img.size
        new_size = (int(w * scale_percent / 100), int(h * scale_percent / 100))
        img = img.resize(new_size, Image.LANCZOS)

    # Encode image to JPEG in memory
    image_stream = io.BytesIO()
    img.save(image_stream, format='JPEG')  # No compression control here
    image_stream.seek(0)

    # Send image bytes to client
    socketio.emit('photo_data', image_stream.read())
    print(f"Photo sent at {scale_percent}% resolution.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
