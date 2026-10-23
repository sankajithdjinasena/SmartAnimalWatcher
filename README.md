# 🐾 Smart Animal Intrusion Detection System (Smart Animal Watcher)

A real-time AI-powered surveillance system that detects animals entering a home or farm environment, classifies them based on threat levels, and dispatches instant security alerts to the property owner's phone number as well as direct coordination with the Wildlife Conservation Emergency Service.

------------------------------------------------------------------------

## 🚀 Key Features

- 🎥 **Real-time Camera Surveillance**: Live MJPEG video stream with YOLOv8 object detection.
- 🧠 **Extended Animal Threat Classification**:
  - 🚨 **Dangerous Wild Animals**: Wild Elephants, Bears, Leopards, Tigers, Venomous Snakes, Crocodiles, Wild Boars, Wolves, Hyenas (triggers instant Owner SMS alert, snapshot capture, and Wildlife Emergency 1992 protocol).
  - ⚠️ **Caution (Property / Troop Threat)**: Monkeys, Baboons (invasive property breaches & crop damage).
  - ✅ **Safe / Non-Dangerous**: Cattle (Cows), Horses, Sheep, Dogs, Cats, Birds, Deer, Zebras.
  - 🚫 Non-animal objects (humans, vehicles, furniture) are safely excluded from animal logs.
- 📱 **Owner Account & Person Number System**:
  - Secure Owner Sign In, Sign Up, and Password Reset.
  - Alerts are dispatched directly to the registered owner's phone number.
- 📞 **Wildlife Conservation Service Integration**:
  - Quick dial hotline (`1992`) and instant emergency incident reporting modal.
- 💬 **Direct Messaging / Alert Dispatch**:
  - Automated threat dispatch & manual test alert messaging.
- 🗑️ **Clear Detection History**:
  - One-click action to clear detection logs and reset active intrusion alarms.
  - Evidence vault snapshot cleanup.
- 📸 **Rate-Limited Threat Snapshots**:
  - Automated evidence capture with cooldown to prevent disk flooding.
- 💻 **Platform Compatible**:
  - Relative-path batch scripts (`app.bat`) for quick launch.

------------------------------------------------------------------------

## 🛠️ Tech Stack

### Backend
- Python 3.10+
- Flask (Web Server & REST APIs)
- OpenCV (Computer Vision & Camera I/O)
- Ultralytics YOLOv8 (Deep Learning Object Detection)
- SQLite3 (Persistent storage for accounts, detection logs, and alert history)

### Frontend
- HTML5 & Jinja2 Templates
- Modern Cyber-Security Dark UI Theme (Custom CSS)
- Vanilla JavaScript (Real-time alert polling & camera stream controls)

### Emergency Services
- SMS / Notification Dispatcher
- Wildlife Conservation Emergency Hotline (1992) & Police (119)

------------------------------------------------------------------------

## 📂 Project Structure

```
├─ app.bat                       # One-click launcher
├─ README.md
├─ requirements.txt              # Clean Python dependencies
└─ application/
    ├─ snapshots/                # Evidence snapshots of critical intrusions
    ├─ static/
    │  └─ css/
    │     └─ style.css           # Global modern responsive stylesheet
    ├─ templates/
    │  ├─ layout.html            # Base template with Wildlife emergency modal
    │  ├─ login.html             # Owner Sign In with Phone/Email
    │  ├─ register.html          # Owner Sign Up with Person Number
    │  ├─ forgot_password.html   # Password recovery
    │  ├─ index.html             # Live surveillance HUD & controls
    │  ├─ logs.html              # Filterable detection audit log
    │  └─ gallery.html           # Threat evidence gallery
    ├─ animal_config.py          # Unified COCO animal threat taxonomy
    ├─ database.py               # SQLite user & detection database
    ├─ alert_service.py          # SMS dispatch & Wildlife alerting
    ├─ app.py                    # Main Flask application
    ├─ detect.py                 # Standalone desktop detection script
    ├─ flask_app.bat             # Batch launcher for Flask server
    └─ yolov8n.pt                # Pretrained YOLOv8 weights
```

------------------------------------------------------------------------

## ⚙️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sankajithdjinasena/SmartAnimalWatcher.git
   cd SmartAnimalWatcher
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   Double-click `app.bat` or run:
   ```bash
   app.bat
   ```
   Or manually:
   ```bash
   cd application
   python app.py
   ```
   Open your browser at `http://127.0.0.1:5000/`.

4. **Demo Account:**
   - **Phone / Identifier**: `0771234567`
   - **Password**: `admin123`
   *(Or sign up with your own phone number on the registration page)*

------------------------------------------------------------------------

## 📜 License
This project is for educational and research purposes.
