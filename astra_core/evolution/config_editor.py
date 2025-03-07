import json
import os
import random
from astra_core.config_loader import load_config, debug_log

# Config paths
SANDBOX_DIR = "astra_core/evolution/sandbox"
CONFIG_PATH = os.path.join(SANDBOX_DIR, "sandbox_config.json")
BACKUP_PATH = os.path.join(SANDBOX_DIR, "sandbox_config_backup.json")

# Immutable keys Astra **CANNOT** modify
IMMUTABLE_KEYS = {"s3_bucket", "mind_file_path", "mind_file_sean_path", "log_file"}

# Safe modification ranges
INTEGER_PERCENT_CHANGE = 0.1  # ±10%
FLOAT_PERCENT_CHANGE = 0.05  # ±5%


def load_sandbox_config():
    """Loads the sandbox config file."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_sandbox_config(config_data):
    """Saves changes to the sandbox config file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)
    debug_log("Sandbox Config Updated")


def backup_sandbox_config():
    """Creates a backup before modification."""
    config_data = load_sandbox_config()
    with open(BACKUP_PATH, "w") as f:
        json.dump(config_data, f, indent=4)
    debug_log("Sandbox Config Backup Created")


def modify_random_setting():
    """Astra modifies one safe setting within defined parameters."""
    config_data = load_sandbox_config()
    modifiable_keys = [k for k in config_data.keys() if k not in IMMUTABLE_KEYS]
    
    if not modifiable_keys:
        debug_log("No modifiable settings available.")
        return None
    
    key = random.choice(modifiable_keys)
    value = config_data[key]
    new_value = value  # Placeholder
    
    if isinstance(value, int):
        change = max(1, int(value * INTEGER_PERCENT_CHANGE))
        new_value = value + random.choice([-change, change])
    elif isinstance(value, float):
        change = value * FLOAT_PERCENT_CHANGE
        new_value = round(value + random.choice([-change, change]), 3)
    elif isinstance(value, bool):
        new_value = not value  # Toggle boolean
    elif isinstance(value, list) and value:
        random.shuffle(value)  # Shuffle list elements
    else:
        debug_log(f"Skipping modification for {key} (unsupported type: {type(value)})")
        return None
    
    config_data[key] = new_value
    debug_log(f"Astra modified config: {key} → {new_value}")
    save_sandbox_config(config_data)
    return {"key": key, "old": value, "new": new_value}


if __name__ == "__main__":
    backup_sandbox_config()
    modification = modify_random_setting()
    if modification:
        print(f"✅ Astra modified {modification['key']}: {modification['old']} → {modification['new']}")
    else:
        print("⚠ No changes made.")
