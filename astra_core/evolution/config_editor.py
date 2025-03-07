import json
import os
from astra_core.config_loader import load_config, debug_log

SANDBOX_DIR = "astra_core/evolution/sandbox"
CONFIG_PATH = os.path.join(SANDBOX_DIR, "sandbox_config.json")

def load_sandbox_config():
    """Loads the sandbox config file"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_sandbox_config(config_data):
    """Saves changes to the sandbox config file"""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)
    debug_log("Sandbox Config Updated")

def modify_config(key, value):
    """Astra's safe way to modify her config"""
    config = load_sandbox_config()
    config[key] = value
    save_sandbox_config(config)
    print(f"✅ Config updated: {key} = {value}")

# Example Test
if __name__ == "__main__":
    modify_config("test_setting", "Hello, Astra!")
