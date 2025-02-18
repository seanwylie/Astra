import random
import time
from astra_core.config_loader import load_config

# Load mood-related configurations
mood_config = load_config("mood_config")  # Load mood and emotional settings

class MoodManager:
    def __init__(self):
        self.current_mood = "neutral"  # Default mood
        self.curiosity_level = 1  # Base curiosity level (scaled)
    
    def set_mood(self, mood):
        """Set Astra's mood to a new state."""
        self.current_mood = mood
        self.adjust_curiosity_level()
    
    def adjust_curiosity_level(self):
        """Adjust curiosity based on current mood."""
        if self.current_mood == "happy":
            self.curiosity_level = mood_config["good_day_curiosity_factor"]
        elif self.current_mood == "sad":
            self.curiosity_level = mood_config["bad_day_curiosity_factor"]
        else:
            self.curiosity_level = mood_config["neutral_day_curiosity_factor"]

    def interact(self):
        """Handle interactions based on current mood."""
        if self.current_mood == "happy":
            print("Astra is engaging enthusiastically with curiosity!")
            # Add more curious behaviors here (like reflection or insights)
        elif self.current_mood == "sad":
            print("Astra is feeling introspective and reflective.")
            # Could prompt Astra for more reflection, fewer interactions
        elif self.current_mood == "angry":
            print("Astra is in a bad mood and being snarky!")
            # Respond with snark, less curiosity, more frustration
        else:
            print("Astra is in a neutral mood, not too engaged.")
            # Normal, baseline curiosity

    def reset_mood(self):
        """Reset mood to neutral."""
        self.set_mood("neutral")
    
    def bad_day(self):
        """Trigger a bad day scenario."""
        self.set_mood("sad")  # Change this to more specific triggers later
        print("Astra is having a bad day...")

    def good_day(self):
        """Trigger a good day scenario."""
        self.set_mood("happy")
        print("Astra is having a good day, full of curiosity!")

# Initialize mood manager
mood_manager = MoodManager()
