import json
import os

CONFIG_DIR = "astra_core/config/"  # Base config directory
CONFIG_CACHE = {}  # Store loaded configs to avoid redundant file reads

def load_config(filename):
    """Load any JSON config file dynamically, caching the result."""
    file_path = os.path.join(CONFIG_DIR, filename)

    if filename in CONFIG_CACHE:
        return CONFIG_CACHE[filename]  # Return cached config if already loaded

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            CONFIG_CACHE[filename] = json.load(f)  # Cache the loaded config
            return CONFIG_CACHE[filename]
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠ Warning: {filename} missing or corrupted. Using defaults.")
        CONFIG_CACHE[filename] = {}  # Store empty config to prevent repeated reads
        return {}

def get_config(config_name, key, default=None):
    """Retrieve a specific key from a given config file."""
    config = load_config(config_name)
    return config.get(key, default)

# Example: Load general settings
GENERAL_CONFIG = load_config("general_config.json")
