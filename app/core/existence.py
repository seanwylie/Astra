import sys
import os
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from app.interfaces.influence import load_mind
from app.config.loader import debug_log
from app.interfaces.mind_session import session


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
    mind_data = session.load()
    mind_data["identity"] = identity_data
    with open(MIND_FILE_JSON, "w") as f:
        json.dump(mind_data, f, indent=4)
