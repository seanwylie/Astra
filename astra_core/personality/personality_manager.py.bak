import json
import os
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage

CONFIG_PATH = "astra_core/config/personality_config.json"
PERSONALITY_PATH = "astra_core/config/personality_state.json"

def load_config():
    """Load personality config."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def load_personality():
    """Load Astra's current personality state."""
    try:
        with open(PERSONALITY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"trait_weights": {}}  # Default empty traits

def get_personality_state():
    """Returns Astra's current personality traits as a dictionary."""
    return load_personality()  # Fetch stored personality traits


def save_personality(personality):
    """Save Astra's updated personality state."""
    with open(PERSONALITY_PATH, "w") as f:
        json.dump(personality, f, indent=4)

def update_personality(event, magnitude=1.0):
    """Modify Astra's personality dynamically based on event triggers."""
    config = load_config()
    personality = load_personality()
    
    trait_effects = config["trait_interactions"]
    min_bound, max_bound = config["trait_bounds"]["min"], config["trait_bounds"]["max"]

    if event in trait_effects:
        for trait, change in trait_effects[event].items():
            if trait not in personality["trait_weights"]:
                personality["trait_weights"][trait] = 1.0  # Default neutral value

            new_value = personality["trait_weights"][trait] + (change * magnitude)
            personality["trait_weights"][trait] = max(min_bound, min(new_value, max_bound))

    save_personality(personality)
