from flask import Flask, send_file
from flask_socketio import SocketIO
import io
from picamera2 import Picamera2
from time import sleep

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
sleep(2)  # Allow camera to warm up

@socketio.on('take_photo')
def handle_take_photo():
    print("Photo request received from desktop.")
    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)
    socketio.emit('photo_data', image_stream.read())
    print("Photo sent to desktop.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
