import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

def load_config(config_name):
    """Load a JSON config file."""
    config_path = os.path.join(CONFIG_DIR, f"{config_name}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found!")

    with open(config_path, "r") as file:
        return json.load(file)
