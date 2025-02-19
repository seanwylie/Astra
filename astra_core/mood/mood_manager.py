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
        mood_config = load_config("mood_config")
        print("🔍 Debug: mood_config Loaded →", mood_config)

        self.LOG_FILE = load_config("general_config").get("log_file", "/home/ubuntu/astra_reflections/astra_logs.json")

        mind_data = load_mind()  # ✅ Load Astra's previous mind state

        # ✅ Restore mood & curiosity level from memory
        self.current_mood = mind_data.get("last_mood", "neutral")
        self.mood_score = mind_data.get("mood_score", 0)
        self.curiosity_level = mind_data.get("curiosity_level", 1.0)  # ✅ Load actual curiosity level

        self.last_mood_update = time.time()

        print(f"🔍 Loaded mood from memory: {self.current_mood}, Score: {self.mood_score}, Curiosity: {self.curiosity_level}")

        self.start_mood_thread()


    def save_mood_state(self):
        """Save Astra's mood and mood score to memory."""
        mind_data = load_mind()
        mind_data["last_mood"] = self.current_mood
        mind_data["mood_score"] = self.mood_score
        save_mind(mind_data)  # ✅ Ensures mood persists across restarts

    def start_mood_thread(self):
        """Runs mood updates periodically in the background."""
        def mood_loop():
            while True:
                time.sleep(600)  # ✅ Check every 10 minutes
                self.update_mood()
        
        thread = threading.Thread(target=mood_loop, daemon=True)
        thread.start()

    def log_mood_change(self):
        """Logs Astra's mood changes and curiosity shifts."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mood": self.current_mood,
            "curiosity_level": self.curiosity_level
        }
        try:
            with open(self.LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"🚨 Log Error: {e}")

    def influence_mood(self, event_type):
        """Gradually shifts Astra's mood based on her experiences."""
        mood_shifts = mood_config.get("mood_influences", {})
        shift_value = mood_shifts.get(event_type, 0)

        self.mood_score += shift_value
        print(f"🔍 Mood influenced by {event_type}: Score now {self.mood_score}")  # ✅ Debugging

        self.update_mood()  # ✅ Ensure mood updates immediately



    def update_mood(self):
        """Gradually updates Astra's mood based on accumulated experiences."""
        elapsed_time = time.time() - self.last_mood_update
        if elapsed_time < 600:  # Ensure updates only happen every 10 minutes
            return

        # Ensure mood score stays within a natural range
        self.mood_score = max(min(self.mood_score, 5), -5)

        # Gradual decay so she doesn’t stay extreme forever
        self.mood_score *= 0.95  # Soft decay

        self.last_mood_update = time.time()

        print(f"🔍 Updating mood... Current: {self.current_mood}, Score: {self.mood_score}")

        if self.mood_score >= 3:
            self.current_mood = "excited"
        elif self.mood_score >= 1:
            self.current_mood = "curious"
        elif self.mood_score <= -2:
            self.current_mood = "frustrated"
        elif self.mood_score <= 0:
            self.current_mood = "thoughtful"

        # ✅ Update curiosity based on new mood
        mind_data = load_mind()
        mind_data["curiosity_level"] = mood_config["moods"].get(self.current_mood, {}).get("curiosity_factor", 1.0)
        save_mind(mind_data)  # ✅ Persist changes

        print(f"🔍 New curiosity level: {mind_data['curiosity_level']}")

        if abs(self.mood_score) >= 5:
            print("💤 Astra is taking a nap to reset emotions...")
            self.mood_score *= 0.5
            self.current_mood = "neutral"

        self.save_mood_state()
        self.log_mood_change()


    def interact(self):
        """Handle interactions based on current mood."""
        if self.current_mood in mood_config["moods"]:
            self.curiosity_level = mood_config["moods"][self.current_mood]["curiosity_factor"]
        else:
            self.curiosity_level = 1.0  # Default to neutral if not found

    def reset_mood(self):
        """Reset mood to neutral."""
        self.mood_score = 0
        self.set_mood("neutral")

    def set_mood(self, mood):
        """Set Astra's mood to a new state and log it persistently."""
        if mood not in mood_config["moods"]:
            print(f"⚠️ Warning: Unknown mood '{mood}', defaulting to 'neutral'")
            mood = "neutral"

        self.current_mood = mood

        # ✅ Load and update stored curiosity level
        mind_data = load_mind()
        mind_data["curiosity_level"] = mood_config["moods"].get(mood, {}).get("curiosity_factor", 1.0)
        mind_data["last_mood"] = mood  # ✅ Persist mood
        save_mind(mind_data)  # ✅ Ensure Astra remembers after restart

        print(f"✅ Mood set to: {self.current_mood}, Curiosity: {mind_data['curiosity_level']}")

        # ✅ Log mood changes
        self.log_mood_change()



# Initialize mood manager
mood_manager = MoodManager()
