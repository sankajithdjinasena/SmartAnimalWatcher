import cv2
from ultralytics import YOLO
from datetime import datetime
import os

# Load YOLOv8 model
model = YOLO("yolov8n.pt")  # lightweight & fast

# Risk classification
dangerous_animals = ["snake", "bear", "elephant", "zebra", "horse", "cow"]
safe_animals = ["dog", "cat", "bird"]

if not os.path.exists("snapshots"):
    os.makedirs("snapshots")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, stream=True)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label.lower() in dangerous_animals:
                risk = "DANGEROUS"
                color = (0, 0, 255)
            else:
                risk = "SAFE"
                color = (0, 255, 0)

            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label.upper()} - {risk}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Save snapshot if dangerous
            if risk == "DANGEROUS":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshots/{label}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)

    cv2.imshow("Animal Intrusion Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
