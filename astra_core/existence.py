import sys
import os
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from astra_interfaces.influence import load_mind
from astra_core.config_loader import debug_log



MIND_FILE_JSON = "mind_file.json"

def load_identity():
    """Loads Astra's core identity and self-awareness data."""
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
            return mind_data.get("identity", {})
    except FileNotFoundError:
        return {"core_values": [], "long_term_goals": []}

def save_identity(identity_data):
    """Saves Astra's self-awareness and identity information."""
    debug_log("Loading")  
    mind_data = load_mind()
    mind_data["identity"] = identity_data
    with open(MIND_FILE_JSON, "w") as f:
        json.dump(mind_data, f, indent=4)
