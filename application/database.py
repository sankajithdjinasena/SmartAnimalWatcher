"""
Database management for Smart Animal Watcher using SQLite.
Handles:
- User accounts (Sign Up, Sign In, Password Reset) with Person Phone Numbers
- Detection History Logs with clearing support
- Instant Alert & Message Dispatch Logs
- Wildlife Emergency Services Config
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Detections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        animal TEXT NOT NULL,
        threat_level TEXT NOT NULL,
        risk TEXT NOT NULL,
        confidence REAL DEFAULT 0.0,
        snapshot TEXT,
        time TEXT NOT NULL,
        notified INTEGER DEFAULT 0
    )
    """)

    # Alert messages table (SMS / Wildlife alerts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        recipient_name TEXT,
        alert_type TEXT NOT NULL,
        animal TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT DEFAULT 'SENT'
    )
    """)

    # App Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Insert default settings if not exists
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('wildlife_hotline', '1992')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('wildlife_service_name', 'Department of Wildlife Conservation')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('emergency_police', '119')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('emergency_ambulance', '1990')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cooldown_seconds', '20')")

    # Seed default property owner account if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_pwd_hash = generate_password_hash("admin123")
        cursor.execute("""
        INSERT INTO users (name, phone, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            "Property Owner",
            "0771234567",
            "owner@animalwatcher.local",
            default_pwd_hash,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()

# ----------------- User Management ----------------- #

def register_user(name, phone, email, password):
    conn = get_db()
    cursor = conn.cursor()
    try:
        pwd_hash = generate_password_hash(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO users (name, phone, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), phone.strip(), email.strip().lower(), pwd_hash, now))
        conn.commit()
        user_id = cursor.lastrowid
        return True, "Registration successful!", user_id
    except sqlite3.IntegrityError as e:
        err_msg = str(e)
        if "phone" in err_msg:
            return False, "This phone number is already registered.", None
        elif "email" in err_msg:
            return False, "This email address is already registered.", None
        return False, "User with this phone or email already exists.", None
    finally:
        conn.close()

def authenticate_user(login_identifier, password):
    """Identifier can be phone number or email"""
    conn = get_db()
    cursor = conn.cursor()
    ident = login_identifier.strip()
    cursor.execute("""
    SELECT * FROM users WHERE phone = ? OR LOWER(email) = ?
    """, (ident, ident.lower()))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return True, dict(user)
    return False, None

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_phone_or_email(identifier):
    conn = get_db()
    cursor = conn.cursor()
    ident = identifier.strip()
    cursor.execute("SELECT * FROM users WHERE phone = ? OR LOWER(email) = ?", (ident, ident.lower()))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def reset_password(identifier, new_password):
    conn = get_db()
    cursor = conn.cursor()
    ident = identifier.strip()
    user = get_user_by_phone_or_email(ident)
    if not user:
        conn.close()
        return False, "No account found matching this phone number or email."
    
    pwd_hash = generate_password_hash(new_password)
    cursor.execute("""
    UPDATE users SET password_hash = ? WHERE id = ?
    """, (pwd_hash, user["id"]))
    conn.commit()
    conn.close()
    return True, "Password reset successfully. You can now log in."

# ----------------- Detection Management ----------------- #

def add_detection(animal, threat_level, risk, confidence=0.0, snapshot="", notified=0):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO detections (animal, threat_level, risk, confidence, snapshot, time, notified)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (animal, threat_level, risk, round(confidence, 2), snapshot, now, notified))
    conn.commit()
    det_id = cursor.lastrowid
    conn.close()
    return det_id

def get_detections(limit=None, risk_filter="all"):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM detections"
    params = []

    if risk_filter in ["dangerous", "critical"]:
        query += " WHERE threat_level IN ('DANGEROUS', 'CRITICAL')"
    elif risk_filter == "caution":
        query += " WHERE threat_level = 'CAUTION'"
    elif risk_filter == "safe":
        query += " WHERE threat_level = 'SAFE'"
    elif risk_filter == "today":
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        query += " WHERE time LIKE ?"
        params.append(f"{today_prefix}%")

    query += " ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_all_detections():
    """Clear all detection logs"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections")
    conn.commit()
    conn.close()
    return True

def get_detection_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM detections")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detections WHERE threat_level IN ('DANGEROUS', 'CRITICAL')")
    dangerous = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detections WHERE threat_level = 'SAFE'")
    safe = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT animal) FROM detections")
    unique_species = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM detections ORDER BY id DESC LIMIT 1")
    latest = cursor.fetchone()

    conn.close()
    return {
        "total": total,
        "dangerous": dangerous,
        "critical": dangerous,
        "safe": safe,
        "unique_species": unique_species,
        "latest": dict(latest) if latest else None
    }

# ----------------- Alert / Message Dispatch ----------------- #

def record_alert(phone, recipient_name, alert_type, animal, message, status="DISPATCHED"):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO alerts (phone, recipient_name, alert_type, animal, message, timestamp, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (phone, recipient_name, alert_type, animal, message, now, status))
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id

def get_recent_alerts(limit=20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_alerts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

# ----------------- Settings ----------------- #

def get_setting(key, default=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def update_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()
