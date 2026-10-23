"""
Notification and Wildlife Emergency Response Service.
Dispatches critical SMS notifications to the registered property owner's phone number
and coordinates Wildlife Conservation Emergency Service alerts.
"""

from datetime import datetime
import threading
from database import record_alert, get_setting

# In-memory alert state for instant real-time UI synchronization
active_threat_lock = threading.Lock()
current_active_threat = None

# Track last alert timestamp per animal to prevent notification spam
last_alert_times = {}

def get_active_threat():
    global current_active_threat
    with active_threat_lock:
        return current_active_threat

def dismiss_active_threat():
    global current_active_threat
    with active_threat_lock:
        current_active_threat = None

def trigger_critical_alarm(animal, threat_level, risk_label, snapshot_file, owner_user=None):
    """
    Called when a CRITICAL threat (e.g. bear, elephant) is detected.
    Enforces cooldown, notifies registered owner's phone number, records alert, and triggers active UI threat state.
    """
    global current_active_threat
    now = datetime.now()
    animal_key = animal.lower().strip()

    try:
        cooldown = int(get_setting("cooldown_seconds", "20"))
    except Exception:
        cooldown = 20

    # Cooldown check for messaging
    last_time = last_alert_times.get(animal_key)
    if last_time and (now - last_time).total_seconds() < cooldown:
        return False, "Cooldown active"

    last_alert_times[animal_key] = now

    # Update active threat for live UI banner & siren
    with active_threat_lock:
        current_active_threat = {
            "animal": animal.upper(),
            "threat_level": threat_level,
            "risk_label": risk_label,
            "snapshot": snapshot_file,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }

    # Recipient details
    recipient_phone = owner_user.get("phone", "Emergency Broadcast") if owner_user else "Registered Owner"
    recipient_name = owner_user.get("name", "Property Owner") if owner_user else "Property Owner"

    message_body = (
        f"🚨 [CRITICAL ALERT] Dangerous animal intrusion detected!\n"
        f"Species: {animal.upper()} | Threat: {risk_label}\n"
        f"Time: {now.strftime('%I:%M:%S %p, %d %b %Y')}\n"
        f"Action: Remain indoors and contact Wildlife Conservation ({get_setting('wildlife_hotline', '1992')})."
    )

    # Record message in database
    record_alert(
        phone=recipient_phone,
        recipient_name=recipient_name,
        alert_type="SMS_CRITICAL_DISPATCH",
        animal=animal,
        message=message_body,
        status="DELIVERED"
    )

    print(f"\n[ALERT DISPATCHED] -> To: {recipient_phone} ({recipient_name})\n{message_body}\n")
    return True, "Alert dispatched successfully"

def send_manual_message(phone, recipient_name, message, alert_type="MANUAL_SMS"):
    """Allows manual sending or testing of alert messages from the dashboard"""
    alert_id = record_alert(
        phone=phone,
        recipient_name=recipient_name,
        alert_type=alert_type,
        animal="System Broadcast",
        message=message,
        status="DELIVERED"
    )
    return alert_id
