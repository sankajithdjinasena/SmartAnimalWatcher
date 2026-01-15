from cProfile import label
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
                    risk = "High"
                    color = (0, 0, 255)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"snapshots/{label}_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                else:
                    risk = "Low"
                    color = (0, 255, 0)

                last_seen = {}
                COOLDOWN = 10  # seconds

                now = datetime.now()
                key = label

                if key not in last_seen or (now - last_seen[key]).seconds > COOLDOWN:
                    logs.append({
                        "animal": label,
                        "risk": risk,
                        "time": now.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    last_seen[key] = now


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
from flask import request
from datetime import datetime, timedelta

@app.route('/logs')
def view_logs():
    page = int(request.args.get('page', 1))
    risk_filter = request.args.get('risk', 'all')

    PER_PAGE = 50

    last_seen = {}
    COOLDOWN = 10  # seconds

    filtered_logs = logs.copy()

    # Sort by latest first
    filtered_logs.sort(
    key=lambda x: datetime.strptime(x['time'], "%Y-%m-%d %H:%M:%S"),
    reverse=True
    )

    # Apply risk filter
    if risk_filter == 'high':
        filtered_logs = [l for l in filtered_logs if l['risk'].lower() == 'high']
    elif risk_filter == 'today':
        today = datetime.now().date()
        filtered_logs = [
            l for l in filtered_logs
            if datetime.strptime(l['time'], "%Y-%m-%d %H:%M:%S").date() == today
        ]
    elif risk_filter == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        filtered_logs = [
            l for l in filtered_logs
            if datetime.strptime(l['time'], "%Y-%m-%d %H:%M:%S") >= week_ago
        ]

    total = len(filtered_logs)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    page_logs = filtered_logs[start:end]
    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    return render_template(
    'logs.html',
    logs=page_logs,          # paginated table data
    all_logs=filtered_logs,  # FULL filtered data (for stats)
    page=page,
    total_pages=total_pages,
    risk_filter=risk_filter
    )


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
