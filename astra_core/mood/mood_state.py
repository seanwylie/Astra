from astra_core.config_loader import load_config

# ✅ Load mood-related configurations
mood_config = load_config("mood_config")

# ✅ Global mood state (stored here instead of `mood_manager.py`)
CURRENT_MOOD = 1.0  # Default mood as a neutral value

def get_current_mood():
    """Retrieve Astra’s current mood dynamically."""
    return CURRENT_MOOD
