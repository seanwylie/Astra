import json

def load_json_file(filename, default_data=None):
    """Safely load a JSON file, returning default data if missing/corrupted."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠ Warning: {filename} not found or corrupted. Using default.")
        return default_data or {}

def save_json_file(filename, data):
    """Safely save data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
