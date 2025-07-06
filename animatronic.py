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

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
sleep(2)

@socketio.on('take_photo')
def handle_take_photo(data=None):
    print("Photo request received from desktop.")
    
    # Default quality
    quality = 85
    if data and isinstance(data, dict):
        quality = int(data.get('quality', 85))
        print(f"Using JPEG quality: {quality}")

    # Capture image to memory
    frame = camera.capture_array()
    img = Image.fromarray(frame)

    # Compress image
    image_stream = io.BytesIO()
    img.save(image_stream, format='JPEG', quality=quality)
    image_stream.seek(0)

    # Send image
    socketio.emit('photo_data', image_stream.read())
    print("Photo sent to desktop.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
