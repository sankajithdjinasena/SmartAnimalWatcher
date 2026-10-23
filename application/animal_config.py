"""
Extended Animal Threat Taxonomy for Smart Animal Watcher.
Includes high-risk predators, venomous reptiles, and destructive wildlife
alongside harmless farm and domestic species.
"""

# Dangerous Wildlife Species (Apex predators, venomous reptiles, crop destroyers)
DANGEROUS_SPECIES = {
    "bear", "elephant", "leopard", "tiger", "lion",
    "snake", "crocodile", "alligator", "wild_boar", "boar",
    "wolf", "hyena"
}

# Caution / Property Threat Species (Invasive troops / crop nuisance)
CAUTION_SPECIES = {
    "monkey", "baboon"
}

# Safe / Non-Dangerous Farm & Domestic Species
SAFE_SPECIES = {
    "cow", "cattle", "horse", "sheep", "dog", "cat", "bird",
    "zebra", "giraffe", "deer"
}

# All recognized animal classes
ALL_ANIMALS = DANGEROUS_SPECIES | CAUTION_SPECIES | SAFE_SPECIES

# Accurate Threat Configurations
THREAT_LEVELS = {
    "DANGEROUS": {
        "animals": DANGEROUS_SPECIES,
        "risk_label": "DANGEROUS",
        "badge_class": "badge-critical",
        "color": (0, 0, 255),        # Red (BGR)
        "trigger_sms": True,
        "trigger_wildlife": True,
        "description": "Lethal predator, venomous reptile, or aggressive wild animal. Poses immediate danger to human life and property."
    },
    "CAUTION": {
        "animals": CAUTION_SPECIES,
        "risk_label": "CAUTION (Property Threat)",
        "badge_class": "badge-moderate",
        "color": (0, 165, 255),      # Orange/Amber (BGR)
        "trigger_sms": False,
        "trigger_wildlife": False,
        "description": "Troop / invasive wildlife causing house breach, food raid, or garden damage."
    },
    "SAFE": {
        "animals": SAFE_SPECIES,
        "risk_label": "SAFE (Non-Dangerous)",
        "badge_class": "badge-safe",
        "color": (0, 255, 0),        # Green (BGR)
        "trigger_sms": False,
        "trigger_wildlife": False,
        "description": "Harmless farm, domestic, or peaceful grazing animal. Poses no threat to humans."
    }
}

# Animal Emojis & Display Names
ANIMAL_METADATA = {
    "bear": {"emoji": "🐻", "name": "Bear"},
    "elephant": {"emoji": "🐘", "name": "Wild Elephant"},
    "leopard": {"emoji": "🐆", "name": "Leopard"},
    "tiger": {"emoji": "🐯", "name": "Tiger"},
    "lion": {"emoji": "🦁", "name": "Lion"},
    "snake": {"emoji": "🐍", "name": "Venomous Snake"},
    "crocodile": {"emoji": "🐊", "name": "Crocodile"},
    "alligator": {"emoji": "🐊", "name": "Alligator"},
    "wild_boar": {"emoji": "🐗", "name": "Wild Boar"},
    "boar": {"emoji": "🐗", "name": "Wild Boar"},
    "wolf": {"emoji": "🐺", "name": "Wolf"},
    "hyena": {"emoji": "🐕", "name": "Hyena"},
    "monkey": {"emoji": "🐒", "name": "Monkey"},
    "baboon": {"emoji": "🐒", "name": "Baboon"},
    "cow": {"emoji": "🐄", "name": "Cow / Cattle"},
    "cattle": {"emoji": "🐄", "name": "Cattle"},
    "horse": {"emoji": "🐎", "name": "Horse"},
    "sheep": {"emoji": "🐑", "name": "Sheep"},
    "dog": {"emoji": "🐕", "name": "Dog"},
    "cat": {"emoji": "🐈", "name": "Cat"},
    "bird": {"emoji": "🐦", "name": "Bird"},
    "zebra": {"emoji": "🦓", "name": "Zebra"},
    "giraffe": {"emoji": "🦒", "name": "Giraffe"},
    "deer": {"emoji": "🦌", "name": "Deer"}
}

def classify_animal(label: str):
    """
    Given a detection label from YOLO:
    Returns (is_animal, threat_level, config)
    If label is not an animal (e.g. human, chair, car), returns (False, None, None)
    """
    clean_label = label.lower().strip().replace(" ", "_")

    if clean_label not in ALL_ANIMALS:
        return False, None, None

    if clean_label in DANGEROUS_SPECIES:
        return True, "DANGEROUS", THREAT_LEVELS["DANGEROUS"]

    if clean_label in CAUTION_SPECIES:
        return True, "CAUTION", THREAT_LEVELS["CAUTION"]

    return True, "SAFE", THREAT_LEVELS["SAFE"]

def get_animal_display(label: str):
    """Returns formatted emoji and display name for UI"""
    clean = label.lower().strip().replace(" ", "_")
    meta = ANIMAL_METADATA.get(clean, {"emoji": "🐾", "name": label.capitalize()})
    return f"{meta['emoji']} {meta['name']}"

def parse_snapshot_info(filename: str):
    """
    Parses snapshot filenames accurately (including multi-word animals like wild_boar)
    and formats human-readable timestamps and threat badges.
    """
    from datetime import datetime
    base = filename.rsplit('.', 1)[0]
    parts = base.split('_')

    # Locate date part (8 digits starting with 20, e.g. 20261023)
    date_idx = -1
    for i, p in enumerate(parts):
        if len(p) == 8 and p.isdigit() and p.startswith("20"):
            date_idx = i
            break

    if date_idx != -1:
        animal_slug = "_".join(parts[:date_idx])
        date_str = parts[date_idx]
        time_str = parts[date_idx + 1] if len(parts) > date_idx + 1 else ""
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            time_display = dt.strftime("%d %b %Y • %I:%M %p")
        except Exception:
            time_display = f"{date_str} {time_str}"
    else:
        animal_slug = parts[0]
        time_display = "Evidence Snapshot"

    is_a, threat_level, cfg = classify_animal(animal_slug)
    if not is_a:
        threat_level = "DANGEROUS"
        cfg = THREAT_LEVELS["DANGEROUS"]

    return {
        "filename": filename,
        "animal": animal_slug,
        "display_name": get_animal_display(animal_slug),
        "time_display": time_display,
        "threat_level": threat_level,
        "badge_class": cfg["badge_class"],
        "risk_label": cfg["risk_label"]
    }
