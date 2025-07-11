import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "settings.json")

def load_settings(path=SETTINGS_FILE):
    """Load settings from a JSON file."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_settings(updates, path=SETTINGS_FILE):
    """Update settings in a JSON file with the provided dictionary."""
    settings = load_settings(path)
    settings.update(updates)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    return settings