from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import serial
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ser = None
connected = False
current_speed = 0.0
current_incline = 0.0

def connect_treadmill():
    global ser, connected
    while True:
        try:
            ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            connected = True
            print("TREADMILL CONNECTED!")
            socketio.emit('status', {'connected': True})
            break
        except:
            connected = False
            print("Waiting for /dev/ttyUSB0 ...")
            time.sleep(3)

def send_command(cmd):
    global ser
    if connected and ser:
        ser.write((cmd + "\n").encode())
        print(f"→ {cmd}")

def read_loop():
    global current_speed, current_incline
    while True:
        if connected and ser:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"← {line}")
                    socketio.emit('data', {'raw': line})
            except:
                pass
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('command')
def handle_command(data):
    cmd = data.get('cmd')
    value = data.get('value')
    if cmd == 'speed' and value is not None:
        send_command(f"SPEED {value:.1f}")
    elif cmd == 'incline' and value is not None:
        send_command(f"INCLINE {int(value)}")
    elif cmd == 'start':
        send_command("START")
    elif cmd == 'stop':
        send_command("STOP")

if __name__ == '__main__':
    threading.Thread(target=connect_treadmill, daemon=True).start()
    threading.Thread(target=read_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
