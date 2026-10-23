"""
Standalone YOLOv8 Real-time Animal Intrusion Detection (Desktop Window Mode).
Aligns with animal_config threat classification and rate-limited snapshot capture.
"""

import os
import cv2
import uuid
from datetime import datetime
from ultralytics import YOLO
from animal_config import classify_animal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Load YOLOv8 model
print(f"Loading YOLOv8 model from {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

def find_working_camera():
    for idx in [2, 1, 0, 3]:
        try:
            c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if c.isOpened():
                ret, frame = c.read()
                c.release()
                if ret and frame is not None and frame.mean() > 5:
                    return idx
        except Exception:
            pass
    return 0

cam_idx = find_working_camera()
print(f"Opening camera index {cam_idx} with DSHOW...")
cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit(1)

last_snapshot_times = {}
COOLDOWN = 15  # seconds

print("\n--- Animal Intrusion Detection Active ---")
print("Press 'q' in the window to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    results = model(frame, verbose=False)
    now = datetime.now()

    for r in results:
        for box in r.boxes:
            cls_idx = int(box.cls[0])
            label = model.names[cls_idx].lower().strip()
            conf = float(box.conf[0])

            # Classify using unified animal config (ignores non-animals)
            is_animal, threat_level, config = classify_animal(label)
            if not is_animal:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = config["color"]
            risk_label = config["risk_label"]

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{label.upper()} [{risk_label}] {int(conf * 100)}%",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

            # Save snapshot if CRITICAL threat with cooldown
            if threat_level == "CRITICAL":
                last_time = last_snapshot_times.get(label)
                if last_time is None or (now - last_time).total_seconds() > COOLDOWN:
                    last_snapshot_times[label] = now
                    uid = uuid.uuid4().hex[:6]
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(SNAPSHOTS_DIR, f"{label}_{timestamp}_{uid}.jpg")
                    cv2.imwrite(filename, frame)
                    print(f"🚨 [CRITICAL THREAT] Snapshot saved: {filename}")

    cv2.imshow("Smart Animal Intrusion Detector (Press Q to exit)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
