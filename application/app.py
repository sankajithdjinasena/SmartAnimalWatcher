from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
from datetime import datetime
import os

app = Flask(__name__)
camera = cv2.VideoCapture(0)
model = YOLO("yolov8n.pt")

dangerous_animals = ["snake", "bear", "elephant", "cow", "horse"]
logs = []

if not os.path.exists("snapshots"):
    os.makedirs("snapshots")

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        results = model(frame)

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls].lower()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if label in dangerous_animals:
                    risk = "DANGEROUS"
                    color = (0, 0, 255)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"snapshots/{label}_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                else:
                    risk = "SAFE"
                    color = (0, 255, 0)

                logs.append({
                    "animal": label,
                    "risk": risk,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label.upper()} - {risk}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def view_logs():
    return render_template('logs.html', logs=logs)

@app.route('/gallery')
def gallery():
    images = os.listdir("snapshots")
    return render_template('gallery.html', images=images)

from flask import send_from_directory

@app.route('/snapshots/<filename>')
def snapshots(filename):
    return send_from_directory('snapshots', filename)


if __name__ == "__main__":
    app.run(debug=True)
