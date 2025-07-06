from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('ping_from_desktop')
def on_ping():
    print("Ping received from desktop.")
    socketio.emit('pong_from_pi', 'pong')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
