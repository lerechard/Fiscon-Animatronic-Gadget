# robot_head_server.py

# Auto-install dependencies
try:
    from flask import Flask, request, jsonify, send_from_directory
    from gpiozero import Servo
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "gpiozero"])
    from flask import Flask, request, jsonify, send_from_directory
    from gpiozero import Servo

import os
import signal
import sys

# Setup servos on GPIO 17 and 18
servo_x = Servo(17)
servo_z = Servo(18)

# Flask app
app = Flask(__name__)

def scale_value(value):
    return (value / 50.0) - 1.0  # maps 0–100 to -1 to 1

@app.route("/")
def serve_ui():
    return HTML_PAGE

@app.route("/move", methods=["POST"])
def move():
    data = request.json
    x = float(data.get("x", 50))
    z = float(data.get("z", 50))

    x = max(0, min(100, x))
    z = max(0, min(100, z))

    servo_x.value = scale_value(x)
    servo_z.value = scale_value(z)

    return jsonify({"status": "moved", "x": x, "z": z})

def cleanup(*args):
    print("Cleaning up...")
    servo_x.detach()
    servo_z.detach()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Inline HTML page with IP set
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Robot Head Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; padding: 20px; }
        .slider-box { margin: 20px 0; }
    </style>
</head>
<body>
    <h2>Robot Head Control</h2>
    <div class="slider-box">
        <label for="xSlider">Left-Right (X)</label><br>
        <input type="range" id="xSlider" min="0" max="100" value="50">
    </div>
    <div class="slider-box">
        <label for="zSlider">Up-Down (Z)</label><br>
        <input type="range" id="zSlider" min="0" max="100" value="50">
    </div>

    <script>
        const xSlider = document.getElementById("xSlider");
        const zSlider = document.getElementById("zSlider");

        function sendPosition() {
            fetch("http://100.81.242.29:5000/move", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    x: xSlider.value,
                    z: zSlider.value
                })
            });
        }

        xSlider.addEventListener("input", sendPosition);
        zSlider.addEventListener("input", sendPosition);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    print("🌐 Hosting on http://100.81.242.29:5000")
    app.run(host="0.0.0.0", port=5000)
