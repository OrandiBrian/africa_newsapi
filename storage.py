import json
import os

DB_FILE = "favorites.json"

def load_favorites():
    """Load favorites from local JSON file."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_favorites(favorites_list):
    """Save favorites list to local JSON file."""
    try:
        with open(DB_FILE, "w") as f:
            json.dump(favorites_list, f)
    except Exception as e:
        print(f"Error saving favorites: {e}")
