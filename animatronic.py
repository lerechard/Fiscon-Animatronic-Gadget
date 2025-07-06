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

# Initialize camera and base config
camera = Picamera2()
base_config = camera.create_still_configuration()
base_size = base_config['size']  # (width, height)
camera.configure(base_config)
camera.start()
sleep(2)

@socketio.on('take_photo')
def handle_take_photo(data=None):
    print("Photo request received from desktop.")

    if data is None:
        data = {}

    # Get the scale from data (10 to 100%)
    try:
        scale_percent = max(10, min(int(data.get('scale', 100)), 100))
    except Exception as e:
        print("Invalid scale value:", e)
        scale_percent = 100

    # Calculate new resolution
    new_width = int(base_size[0] * scale_percent / 100)
    new_height = int(base_size[1] * scale_percent / 100)

    print(f"Setting camera resolution to {new_width}x{new_height} ({scale_percent}%)")

    try:
        # Create and apply new configuration
        new_config = camera.create_still_configuration(size=(new_width, new_height))
        camera.configure(new_config)
        camera.start(show_preview=False)
        sleep(0.2)  # Allow camera to adjust

        # Capture to memory buffer
        image_stream = io.BytesIO()
        camera.capture_file(image_stream, format='jpeg')
        image_stream.seek(0)

        # Emit image to client
        socketio.emit('photo_data', image_stream.read())
        print(f"Photo sent at {new_width}x{new_height}")

    except Exception as e:
        print("Failed to capture and send photo:", e)

    # Restore original configuration
    camera.configure(base_config)
    camera.start(show_preview=False)
    sleep(0.2)

if __name__ == '__main__':
    print("Starting Flask-SocketIO server on port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000)
