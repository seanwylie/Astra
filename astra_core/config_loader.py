import json
import os

def load_config(config_file):
    """Load the configuration file from the astra_core/config folder."""
    # Use the absolute path to config/ folder under astra_core
    config_path = os.path.join(os.path.dirname(__file__), 'config', f"{config_file}.json")

    try:
        # Open the config file and return its contents as a dictionary
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {config_path} not found!")
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding the config file {config_path}.")
    
    with open(config_path, "r") as file:
        return json.load(file)
