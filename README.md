# 🐾 Smart Animal Intrusion Detection System (Smart Animal Watcher)

A real-time AI-powered surveillance system that detects animals entering
a home environment, classifies them as safe or dangerous, and sends
instant email alerts for potential threats. This system uses a webcam,
YOLO object detection, and a Flask-based web dashboard.

------------------------------------------------------------------------

## 🚀 Features

-   🎥 Real-time webcam-based detection
-   🧠 AI-powered animal classification (YOLOv8)
-   ⚠️ Risk labeling: Safe / Dangerous
-   🌐 Web dashboard (Flask)
-   📸 Automatic snapshot capture
-   🕒 Detection logs with timestamps
-   💻 Windows-compatible

------------------------------------------------------------------------

## 🛠️ Tech Stack

### Backend

-   Python
-   OpenCV
-   YOLOv8 (Ultralytics)
-   Flask

### Frontend

-   HTML
-   CSS
-   JavaScript

### Notifications

-   Gmail SMTP (Email alerts) # On process

------------------------------------------------------------------------

## 📂 Project Structure
├─ app.bat                       # Optional batch to run everything
├─ README.md
├─ requirements.txt
└─ application/
    ├─ __pycache__/                # Python cache
    ├─ snapshots/                   # Saved snapshots of detected animals
    ├─ templates/
    │  ├─ css/
    │  │  ├─ gallery.css
    │  │  ├─ index.css
    │  │  └─ logs.css
    │  ├─ gallery.html
    │  ├─ index.html
    │  └─ logs.html
    ├─ app.py                        # Main Flask application
    ├─ detect.py                     # YOLO detection script
    ├─ flask_app.bat                 # Batch file to run Flask app
    └─ yolov8n.pt                    # Pretrained YOLOv8 model
    

------------------------------------------------------------------------

## ⚙️ Installation

1.  Clone the repository\
    `git clone https://github.com/sankajithdjinasena/SmartAnimalWatcher.git`

2.  Navigate to the project folder\
    `cd SmartAnimalWatcher`

3.  Install required packages\
    `pip install ultralytics opencv-python flask numpy`

4.  Run the detection script\
    `run app.bat`

------------------------------------------------------------------------

## 📸 How It Works

1.  The webcam captures live video.
2.  YOLOv8 detects animals in real time.
3.  Each detected animal is classified as safe or dangerous.
4.  If a dangerous animal is detected:
    -   A snapshot is saved
    -   An email alert is sent
    -   The event is logged

------------------------------------------------------------------------

## 🧪 Example Use Cases

-   Home safety monitoring
-   Rural & wildlife-prone areas
-   Farm surveillance
-   Smart home systems
-   AI-based security projects

------------------------------------------------------------------------

## 🔮 Future Enhancements

-   Mobile app integration
-   Telegram / WhatsApp alerts
-   Cloud storage for logs
-   Night vision support
-   Custom model training for local animals
-   Sound alarm system

------------------------------------------------------------------------

## 👨‍💻 Author

Developed by **Sankajith D. Jinasena**\

------------------------------------------------------------------------

## 📜 License

This project is for educational and research purposes.
