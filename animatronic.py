try:
    import flask
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'flask', 'flask-socketio', 'eventlet'])

try:
    from picamera2 import Picamera2
except ImportError:
    import subprocess
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-picamera2'])
    exit("Re-run the script after installing Picamera2.")

from flask import Flask, request
from flask_socketio import SocketIO, emit
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
def handle_take_photo():
    client_sid = request.sid  # Get the session ID of the requesting client
    print(f"Photo request received from {client_sid}")

    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)
    image_bytes = image_stream.read()

    # Send photo only to the requesting client
    socketio.emit('photo_data', image_bytes, room=client_sid)
    print(f"Photo sent to {client_sid}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
