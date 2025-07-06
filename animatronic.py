from flask import Flask
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Handle message from desktop
@socketio.on('chat_message')
def handle_message(data):
    print(f"{data['sender']}: {data['message']}")
    # Broadcast to everyone including desktop
    emit('chat_message', {'sender': data['sender'], 'message': data['message']}, broadcast=True)

def terminal_input_loop():
    while True:
        msg = input("You (Pi): ")
        socketio.emit('chat_message', {'sender': 'Pi', 'message': msg})

if __name__ == '__main__':
    threading.Thread(target=terminal_input_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
