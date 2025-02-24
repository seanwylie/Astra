import time
import json
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage

# Load mood-related configurations
mood_config = load_config("mood_config")  # Load mood and emotional settings

class MoodManager:
    def __init__(self):
        print("🔍 Debug: Attempting to load mood_config.json...")
        self.mood_config = load_config("mood_config")
        print("🔍 Debug: mood_config Loaded →", self.mood_config)

        self.LOG_FILE = load_config("general_config").get("log_file", "/home/ubuntu/astra_logs.json")

        mind_data = load_mind()  # ✅ Load Astra's previous mind state

        # ✅ Restore mood & curiosity level from memory
        self.current_mood = mind_data.get("last_mood", "neutral")
        self.mood_score = float(mind_data.get("mood_score", 0))  # Ensure mood score is a float
        self.curiosity_level = mind_data.get("curiosity_level", 1.0)  # ✅ Load actual curiosity level
        self.mood_history = mind_data.get("mood_history", {})  # ✅ Track how long she's been in each mood

        self.last_mood_update = time.time()

        print(f"🔍 Loaded mood from memory: {self.current_mood}, Score: {self.mood_score}, Curiosity: {self.curiosity_level}")

        self.start_mood_thread()

    def save_mood_state(self):
        """Save Astra's mood, mood score, and mood history to memory."""
        mind_data = load_mind()
        mind_data["last_mood"] = self.current_mood
        mind_data["mood_score"] = self.mood_score
        mind_data["mood_history"] = self.mood_history  # ✅ Save mood tracking history
        save_mind(mind_data)

    def start_mood_thread(self):
        """Runs mood updates periodically in the background."""
        def mood_loop():
            while True:
                time.sleep(600)  # ✅ Check every 10 minutes
                self.update_mood()
        
        thread = threading.Thread(target=mood_loop, daemon=True)
        thread.start()

    def influence_mood(self, event_type, amount=None):
        """Gradually shifts Astra's mood based on experiences."""
        if amount is not None:
            shift_value = float(amount)
        else:
            mood_shifts = self.mood_config.get("mood_influences", {})
            shift_value = mood_shifts.get(event_type, 0)
        
        # Adjust mood score based on the shift value
        self.mood_score += shift_value

        # Prevent over/under-shooting mood limits
        self.mood_score = max(min(self.mood_score, 1.0), -1.0)

        print(f"🔍 Mood influenced by {event_type}: New Score: {self.mood_score}")
        self.update_mood()

    def modify_mood_influence(self, event_type, new_value):
        """Allows Astra to modify her mood influences within safe limits."""
        safe_limits = self.mood_config.get("mood_influence_limits", {"min": -2.0, "max": 2.0})
        new_value = max(min(new_value, safe_limits["max"]), safe_limits["min"])
        
        if event_type in self.mood_config.get("mood_influences", {}):
            self.mood_config["mood_influences"][event_type] = new_value
            print(f"🔍 Modified mood influence: {event_type} → {new_value}")
        else:
            print(f"⚠️ Warning: Unknown mood influence '{event_type}', modification skipped.")

    def update_mood(self):
        """Updates Astra's mood dynamically based on stored mood settings."""
        elapsed_time = time.time() - self.last_mood_update
        if elapsed_time < 5:
            return

        previous_mood = self.current_mood

        # ✅ Get mood settings from config
        mood_settings = self.mood_config.get("moods", {})
        
        # ✅ Sort moods by curiosity factor (highest to lowest)
        sorted_moods = sorted(mood_settings.items(), key=lambda x: -x[1].get("curiosity_factor", 1.0))

        # ✅ Determine Astra's mood dynamically
        for mood, attributes in sorted_moods:
            curiosity_threshold = attributes.get("curiosity_factor", 1.0)  # Use curiosity_factor as a threshold
            if self.mood_score >= curiosity_threshold:
                self.current_mood = mood
                break

        # ✅ Track how long she's been in each mood
        if previous_mood == self.current_mood:
            self.mood_history[self.current_mood] = self.mood_history.get(self.current_mood, 0) + elapsed_time
        else:
            print(f"🔄 Mood Shifted! {previous_mood} → {self.current_mood}")
            self.mood_history[self.current_mood] = 0  # Reset counter for new mood

        self.last_mood_update = time.time()
        self.save_mood_state()
        print(f"🔍 Updated Mood History: {self.mood_history}")

    def get_mood_history(self):
        """Returns Astra's mood history to analyze trends."""
        return self.mood_history

    def get_current_mood(self):
        """Retrieve Astra’s current mood state.""" 
        return self.current_mood

    def get_curiosity(self):
        """Retrieve Astra's current curiosity level.""" 
        return self.curiosity_level  # Default to 1.0 if missing

# ✅ Initialize mood manager
mood_manager = MoodManager()
