"""
Animal Classifier Configuration for YOLOv8 (COCO Dataset).
Strictly separates DANGEROUS animals from SAFE / Non-Dangerous farm and domestic animals.
All non-animal classes (people, vehicles, objects) are ignored.
"""

# Supported YOLOv8 COCO animal classes
COCO_ANIMALS = {
    "bear", "elephant",
    "cow", "horse", "zebra", "giraffe", "sheep", "dog", "cat", "bird"
}

# Accurate Threat Categories
THREAT_LEVELS = {
    "DANGEROUS": {
        "animals": {"bear", "elephant"},
        "risk_label": "DANGEROUS",
        "badge_class": "badge-critical",
        "color": (0, 0, 255),       # Red (BGR)
        "trigger_sms": True,
        "trigger_wildlife": True,
        "description": "Wild high-risk animal (Apex predator or wild megafauna). Poses direct danger to life and property."
    },
    "SAFE": {
        "animals": {"cow", "horse", "zebra", "giraffe", "sheep", "dog", "cat", "bird"},
        "risk_label": "SAFE (Non-Dangerous)",
        "badge_class": "badge-safe",
        "color": (0, 255, 0),       # Green (BGR)
        "trigger_sms": False,
        "trigger_wildlife": False,
        "description": "Non-dangerous farm, domestic, or peaceful grazing animal. Harmless to humans."
    }
}

# Emoji lookup for UI
ANIMAL_EMOJIS = {
    "bear": "🐻",
    "elephant": "🐘",
    "cow": "🐄",
    "horse": "🐎",
    "zebra": "🦓",
    "giraffe": "🦒",
    "sheep": "🐑",
    "dog": "🐕",
    "cat": "🐈",
    "bird": "🐦"
}

def classify_animal(label: str):
    """
    Given a detection label from YOLO:
    Returns (is_animal, threat_level, config)
    If label is not an animal, returns (False, None, None)
    """
    label = label.lower().strip()
    if label not in COCO_ANIMALS:
        return False, None, None
    
    if label in THREAT_LEVELS["DANGEROUS"]["animals"]:
        return True, "DANGEROUS", THREAT_LEVELS["DANGEROUS"]
    
    return True, "SAFE", THREAT_LEVELS["SAFE"]
