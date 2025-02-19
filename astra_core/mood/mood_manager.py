import time
import json
import threading
from astra_core.config_loader import load_config

# Load mood-related configurations
mood_config = load_config("mood_config")  # Load mood and emotional settings

class MoodManager:
    def __init__(self):
        self.current_mood = "neutral"  # Default mood
        self.curiosity_level = 1  # Base curiosity level (scaled)
        self.LOG_FILE = load_config("general_config")["log_file"]
        self.mood_score = 0  # Track mood influence over time
        self.last_mood_update = time.time()  # Timestamp for gradual mood shifts

        # ✅ Start background mood updates
        self.start_mood_thread()

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
        shift_value = mood_shifts.get(event_type, 0)  # Default to 0 if event is unknown

        self.mood_score += shift_value  # ✅ Apply shift only once
        self.update_mood()  # ✅ Ensure mood updates gradually


    def update_mood(self):
        """Gradually updates Astra's mood based on accumulated experiences."""
        elapsed_time = time.time() - self.last_mood_update
        if elapsed_time < 600:  # Ensure updates only happen every 10 minutes
            return

        self.last_mood_update = time.time()

        # Limit max mood shift per update cycle
        self.mood_score = max(min(self.mood_score, 5), -5)  # Keeps mood range from -5 to +5

        # Define mood ranges based on mood score
        if self.mood_score >= 4:
            self.current_mood = "excited"
        elif self.mood_score >= 2:
            self.current_mood = "curious"
        elif self.mood_score <= -3:
            self.current_mood = "frustrated"
        elif self.mood_score <= -1:
            self.current_mood = "thoughtful"
        else:
            self.current_mood = "neutral"

        # Slow mood decay for more natural shifts
        self.mood_score *= 0.95  # Decay instead of a hard reset

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
        """Set Astra's mood to a new state and log it."""
        if mood not in mood_config["moods"]:
            print(f"⚠️ Warning: Unknown mood '{mood}', defaulting to 'neutral'")
            mood = "neutral"

        self.current_mood = mood
        self.curiosity_level = mood_config["moods"][mood]["curiosity_factor"]

        # ✅ Log mood changes
        self.log_mood_change()


# Initialize mood manager
mood_manager = MoodManager()
