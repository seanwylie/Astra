import json
import os

# Determine the base directory where Astra is running
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Moves up from utils/
ASTRA_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))  # Moves up to project root

# Allow overriding config directory via environment variable
CONFIG_DIR = os.getenv("ASTRA_CONFIG_DIR", os.path.join(ASTRA_DIR, "astra_core/config"))

CONFIG_CACHE = {}

def load_config(filename):
    """Load a JSON config file dynamically, ensuring it always appends `.json`."""
    if not filename.endswith(".json"):
        filename += ".json"  # ✅ Ensure file has the `.json` extension

    file_path = os.path.join(CONFIG_DIR, filename)

    if filename in CONFIG_CACHE:
        return CONFIG_CACHE[filename]  # ✅ Return cached version if already loaded

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            CONFIG_CACHE[filename] = json.load(f)  # ✅ Store in cache for faster access
            return CONFIG_CACHE[filename]
    except FileNotFoundError:
        print(f"⚠ Warning: {filename} not found in {CONFIG_DIR}. Using defaults.")
    except json.JSONDecodeError:
        print(f"❌ Error: {filename} is corrupted. Using defaults.")

    CONFIG_CACHE[filename] = {}  # ✅ Prevent repeated failures
    return CONFIG_CACHE[filename]

def get_config(key, default=None, config_file="general_config.json"):
    """Retrieve a key from a given config file, ensuring it exists."""
    config = load_config(config_file)

    if key not in config:
        print(f"⚠ Warning: Missing key '{key}' in {config_file}. Using default: {default}")

    return config.get(key, os.getenv(key.upper(), default))  # ✅ Uses env fallback if missing
