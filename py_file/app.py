from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
from datetime import datetime

app = Flask(__name__)
camera = cv2.VideoCapture(0)
model = YOLO("yolov8n.pt")

dangerous_animals = ["snake", "bear", "elephant", "cow", "horse"]

logs = []

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
                else:
                    risk = "SAFE"
                    color = (0, 255, 0)

                text = f"{label.upper()} - {risk}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                logs.append({
                    "animal": label,
                    "risk": risk,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def view_logs():
    return render_template('logs.html', logs=logs)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
