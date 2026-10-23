"""
Smart Animal Intrusion Detection System (Smart Animal Watcher)
Main Flask Application with Real-Time YOLOv8 Detection, Thread-Safe Streaming,
Owner SMS Alerts, Authentication, and Wildlife Emergency Response.
"""

import os
import cv2
import time
import uuid
import threading
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, Response, request,
    redirect, url_for, session, flash, jsonify, send_from_directory
)
from ultralytics import YOLO

# Project modules
from animal_config import (
    classify_animal, get_animal_display, parse_snapshot_info,
    DANGEROUS_SPECIES, SAFE_SPECIES
)
from database import (
    init_db, register_user, authenticate_user, reset_password,
    get_user_by_id, add_detection, get_detections, clear_all_detections,
    get_detection_stats, record_alert, get_setting
)
from alert_service import (
    get_active_threat, dismiss_active_threat,
    trigger_critical_alarm, send_manual_message
)

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

if not os.path.exists(SNAPSHOTS_DIR):
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Initialize Flask App & Database
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "animal_watcher_super_secret_key_2026")
app.jinja_env.globals.update(
    get_animal_display=get_animal_display,
    parse_snapshot_info=parse_snapshot_info
)
init_db()

# Load YOLO Model
print(f"Loading YOLOv8 model from {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

# Cooldown tracking: last logged detection timestamp per animal species
last_detection_times = {}
DETECTION_COOLDOWN = 15  # seconds

# Camera Thread Safety and State
camera_lock = threading.RLock()
camera_running = True
camera_instance = None
current_camera_index = None

def auto_detect_camera():
    """Scans for active video capture device with non-black output"""
    for idx in [2, 1, 0, 3]:
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None and frame.mean() > 5:
                    print(f"[CAMERA] Found active camera at index {idx} (mean brightness: {frame.mean():.1f})")
                    return idx
        except Exception:
            pass
    return 0

def get_camera():
    global camera_instance, current_camera_index
    with camera_lock:
        if camera_instance is not None and camera_instance.isOpened():
            return camera_instance

        if current_camera_index is None:
            current_camera_index = auto_detect_camera()

        print(f"[CAMERA] Opening camera device index {current_camera_index} with cv2.CAP_DSHOW...")
        camera_instance = cv2.VideoCapture(current_camera_index, cv2.CAP_DSHOW)
        
        if not camera_instance.isOpened():
            print(f"[WARNING] Could not open camera {current_camera_index}. Trying fallback index 0...")
            camera_instance = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
        return camera_instance

def release_camera():
    global camera_instance
    with camera_lock:
        if camera_instance and camera_instance.isOpened():
            camera_instance.release()
        camera_instance = None

# Authentication Helper Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access security surveillance.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- Video Frame Generator ----------------- #

def generate_frames(owner_id=None):
    """MJPEG stream generator with YOLO inference and rate-limited detection alerts"""
    global camera_running, last_detection_times
    cap = get_camera()

    # Pre-fetch owner details so session is not accessed inside generator loop
    current_owner = get_user_by_id(owner_id) if owner_id else None

    while True:
        if not camera_running:
            # Standby frame when camera is turned off by user
            standby = cv2.imread(os.path.join(BASE_DIR, "static", "standby.jpg")) if os.path.exists(os.path.join(BASE_DIR, "static", "standby.jpg")) else None
            if standby is None:
                import numpy as np
                standby = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(standby, "CAMERA SURVEILLANCE PAUSED", (80, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 170, 255), 2)
            ret, buffer = cv2.imencode(".jpg", standby)
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.5)
            continue

        with camera_lock:
            if cap is None or not cap.isOpened():
                cap = get_camera()
            success, frame = cap.read() if cap else (False, None)

        if not success or frame is None:
            # Fallback standby placeholder if physical camera is unplugged/busy
            import numpy as np
            standby = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(standby, "WAITING FOR CAMERA HARDWARE...", (80, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 229, 255), 2)
            ret, buffer = cv2.imencode(".jpg", standby)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            time.sleep(0.5)
            continue

        # Run YOLO inference
        results = model(frame, verbose=False)
        now = datetime.now()

        for r in results:
            for box in r.boxes:
                cls_idx = int(box.cls[0])
                label = model.names[cls_idx].lower().strip()
                conf = float(box.conf[0])

                # Filter strictly for real COCO animal classes
                is_animal, threat_level, config = classify_animal(label)
                if not is_animal:
                    continue  # Ignore humans, vehicles, chairs, etc.

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = config["color"]
                risk_label = config["risk_label"]

                # Check rate-limit cooldown per animal
                last_time = last_detection_times.get(label)
                should_log = (last_time is None) or ((now - last_time).total_seconds() > DETECTION_COOLDOWN)

                snapshot_filename = ""
                if should_log:
                    last_detection_times[label] = now

                    # If DANGEROUS (e.g. bear, elephant), save snapshot and alert owner
                    if threat_level in ["DANGEROUS", "CRITICAL"]:
                        uid = uuid.uuid4().hex[:6]
                        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
                        snapshot_filename = f"{label}_{timestamp_str}_{uid}.jpg"
                        filepath = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                        cv2.imwrite(filepath, frame)

                        # Trigger critical alarm & SMS dispatch
                        trigger_critical_alarm(
                            animal=label,
                            threat_level="DANGEROUS",
                            risk_label=risk_label,
                            snapshot_file=snapshot_filename,
                            owner_user=current_owner
                        )

                    # Record detection in persistent SQLite database
                    add_detection(
                        animal=label,
                        threat_level=threat_level,
                        risk=risk_label,
                        confidence=conf,
                        snapshot=snapshot_filename,
                        notified=1 if threat_level in ["DANGEROUS", "CRITICAL"] else 0
                    )

                # Draw high-visibility bounding box and label overlay
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                tag_text = f"{label.upper()} [{risk_label.upper()}] {int(conf * 100)}%"
                (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, y1 - 25), (x1 + tw + 10, y1), color, -1)
                cv2.putText(frame, tag_text, (x1 + 5, y1 - 7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

# ----------------- Auth Routes ----------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        success, user = authenticate_user(identifier, password)
        if success:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_phone"] = user["phone"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}! Surveillance system connected.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid phone number / email or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        success, msg, user_id = register_user(name, phone, email, password)
        if success:
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_phone"] = phone
            session["user_email"] = email
            flash(f"Account registered successfully! Critical SMS alerts configured for {phone}.", "success")
            return redirect(url_for("index"))
        else:
            flash(msg, "danger")

    return render_template("register.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("forgot_password.html")

        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "danger")
            return render_template("forgot_password.html")

        success, msg = reset_password(identifier, new_password)
        if success:
            flash(msg, "success")
            return redirect(url_for("login"))
        else:
            flash(msg, "danger")

    return render_template("forgot_password.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))

# ----------------- Dashboard & Surveillance Routes ----------------- #

@app.route("/")
@login_required
def index():
    stats = get_detection_stats()
    recent = get_detections(limit=5)
    active = get_active_threat()
    return render_template(
        "index.html",
        stats=stats,
        recent_detections=recent,
        active_threat=active,
        current_camera_index=current_camera_index if current_camera_index is not None else 0
    )

@app.route("/switch_camera", methods=["POST"])
@login_required
def switch_camera():
    global current_camera_index, camera_instance
    cam_id = request.form.get("camera_index", "auto")
    with camera_lock:
        if camera_instance and camera_instance.isOpened():
            camera_instance.release()
        camera_instance = None
        if cam_id == "auto":
            current_camera_index = auto_detect_camera()
        else:
            current_camera_index = int(cam_id)
        get_camera()
    flash(f"Switched surveillance source to Camera Device #{current_camera_index}.", "info")
    return redirect(url_for("index"))

@app.route("/simulate_threat/<animal>", methods=["POST"])
@login_required
def simulate_threat(animal):
    animal = animal.lower().strip()
    is_a, threat_level, config = classify_animal(animal)
    if not is_a:
        flash(f"'{animal}' is not a valid animal species.", "warning")
        return redirect(url_for("index"))

    current_owner = get_user_by_id(session.get("user_id"))
    uid = uuid.uuid4().hex[:6]
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"{animal}_{timestamp_str}_{uid}.jpg"
    
    import numpy as np
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    color = config["color"]
    cv2.rectangle(test_img, (40, 40), (600, 440), color, 3)
    cv2.putText(test_img, f"DETECTED: {animal.upper()} [{config['risk_label']}]",
                (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.imwrite(os.path.join(SNAPSHOTS_DIR, snapshot_filename), test_img)

    if threat_level in ["DANGEROUS", "CRITICAL"]:
        trigger_critical_alarm(
            animal=animal,
            threat_level="DANGEROUS",
            risk_label=config["risk_label"],
            snapshot_file=snapshot_filename,
            owner_user=current_owner
        )
        flash(f"🚨 CRITICAL ALERT TRIGGERED: Dangerous {animal.upper()} simulated! SMS sent to {session.get('user_phone')}.", "danger")
    elif threat_level == "CAUTION":
        flash(f"⚠️ PROPERTY CAUTION: {animal.upper()} detected. Invasive troop/property threat recorded (no emergency siren).", "warning")
    else:
        flash(f"ℹ️ SAFE SPECIES RECORDED: {animal.upper()} is classified as SAFE / Non-Dangerous farm animal. No emergency alert triggered.", "success")

    add_detection(
        animal=animal,
        threat_level=threat_level,
        risk=config["risk_label"],
        confidence=0.96,
        snapshot=snapshot_filename,
        notified=1 if threat_level in ["DANGEROUS", "CRITICAL"] else 0
    )

    return redirect(url_for("index"))

@app.route("/video_feed")
@login_required
def video_feed():
    owner_id = session.get("user_id")
    return Response(
        generate_frames(owner_id=owner_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/logs")
@login_required
def view_logs():
    page = int(request.args.get("page", 1))
    risk_filter = request.args.get("risk", "all")
    PER_PAGE = 25

    all_filtered = get_detections(risk_filter=risk_filter)
    total = len(all_filtered)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_logs = all_filtered[start:end]

    stats = get_detection_stats()

    return render_template(
        "logs.html",
        logs=page_logs,
        total=total,
        page=page,
        total_pages=total_pages,
        risk_filter=risk_filter,
        stats=stats
    )

@app.route("/gallery")
@login_required
def gallery():
    files = []
    if os.path.exists(SNAPSHOTS_DIR):
        all_files = os.listdir(SNAPSHOTS_DIR)
        valid_extensions = (".jpg", ".jpeg", ".png")
        files = [f for f in all_files if f.lower().endswith(valid_extensions)]
        files.sort(reverse=True)

    return render_template("gallery.html", images=files)

@app.route("/snapshots/<filename>")
@login_required
def snapshots(filename):
    return send_from_directory(SNAPSHOTS_DIR, filename)

# ----------------- Actions & Alerts ----------------- #

@app.route("/clear_detections", methods=["POST"])
@login_required
def clear_detections():
    clear_all_detections()
    dismiss_active_threat()
    flash("All detection logs have been cleared successfully.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/clear_snapshots", methods=["POST"])
@login_required
def clear_snapshots():
    count = 0
    if os.path.exists(SNAPSHOTS_DIR):
        for f in os.listdir(SNAPSHOTS_DIR):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    os.remove(os.path.join(SNAPSHOTS_DIR, f))
                    count += 1
                except Exception as e:
                    print(f"Error removing {f}: {e}")
    flash(f"Cleared {count} snapshot evidence files from storage.", "success")
    return redirect(url_for("gallery"))

@app.route("/delete_snapshot/<filename>", methods=["POST"])
@login_required
def delete_snapshot(filename):
    filepath = os.path.join(SNAPSHOTS_DIR, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            flash(f"Snapshot '{filename}' removed.", "info")
        except Exception as e:
            flash(f"Failed to delete snapshot: {e}", "danger")
    return redirect(url_for("gallery"))

@app.route("/dismiss_threat", methods=["POST"])
@login_required
def dismiss_threat():
    dismiss_active_threat()
    return jsonify({"status": "dismissed"})

@app.route("/send_owner_message", methods=["POST"])
@login_required
def send_owner_message():
    phone = request.form.get("phone", session.get("user_phone", ""))
    name = request.form.get("name", session.get("user_name", "Owner"))
    message = request.form.get("message", "").strip()

    if message:
        send_manual_message(phone, name, message)
        flash(f"SMS security notification dispatched successfully to {name} ({phone})!", "success")
    else:
        flash("Message body cannot be empty.", "warning")

    return redirect(request.referrer or url_for("index"))

@app.route("/dispatch_wildlife_report", methods=["POST"])
@login_required
def dispatch_wildlife_report():
    details = request.form.get("incident_details", "").strip()
    hotline = get_setting("wildlife_hotline", "1992")
    service_name = get_setting("wildlife_service_name", "Department of Wildlife Conservation")

    report_text = f"🚨 WILDLIFE EMERGENCY REPORT to {service_name} ({hotline}):\n{details}"
    record_alert(
        phone=hotline,
        recipient_name=service_name,
        alert_type="WILDLIFE_INCIDENT_REPORT",
        animal="Dangerous Wildlife",
        message=report_text,
        status="DISPATCHED"
    )

    flash(f"Emergency incident report dispatched to {service_name} (Hotline {hotline})!", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/api/status")
@login_required
def api_status():
    return jsonify({
        "active_threat": get_active_threat(),
        "owner_phone": session.get("user_phone", "")
    })

# ----------------- Application Entrypoint ----------------- #

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        release_camera()
