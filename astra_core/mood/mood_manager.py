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

        # ✅ Define a smooth transition between moods instead of sudden jumps
        self.mood_levels = {
            "frustrated": -1.0,
            "neutral": 0.0,
            "curious": 0.5,
            "excited": 1.0,
            "thoughtful": 0.3
        }

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

    def influence_mood(self, event_type, amount=None):
        """Gradually shifts Astra's mood based on her experiences."""

        # ✅ Allow specific adjustments (e.g., encouragement boosts)
        if amount is not None:
            shift_value = amount
        else:
            mood_shifts = mood_config.get("mood_influences", {})
            shift_value = mood_shifts.get(event_type, 0)

        # ✅ Mood scaling: Diminishing returns as mood nears max
        if self.mood_score >= 0.9 and shift_value > 0:
            shift_value *= (1.0 - self.mood_score)  # Slows growth near max

        # ✅ Stronger hit on negative mood shifts
        if event_type == "positive_feedback":
            shift_value *= 1.2  # Slight boost to positive influence
        elif event_type == "negative_feedback":
            shift_value *= 2.5  # Hits **harder** on negatives

        self.mood_score += shift_value
        self.mood_score = max(-1, min(1, self.mood_score))  # ✅ Keep in range

        print(f"🔍 Mood influenced by {event_type}: Score now {self.mood_score}")

        self.update_mood()  # ✅ Ensure mood updates immediately

    def update_mood(self):
        """Updates Astra's mood based on accumulated experiences, ensuring proper mood shifts."""
        elapsed_time = time.time() - self.last_mood_update
        if elapsed_time < 600:  # Only update every 10 minutes
            return

        previous_mood = self.current_mood

        # 🔹 **Ensure Astra's mood updates dynamically**
        if self.mood_score >= 1:
            self.current_mood = "excited"  # **Fully energized**
        elif self.mood_score >= 0.6:
            self.current_mood = "curious"  # **High energy, eager to learn**
        elif self.mood_score >= 0.3:
            self.current_mood = "thoughtful"  # **More introspective**
        elif self.mood_score < 0:
            self.current_mood = "frustrated"  # **Negative mood state**
        else:
            self.current_mood = "neutral"  # Default state

        self.last_mood_update = time.time()

        # ✅ **Slow Astra down if she’s maxed out on mood extremes**
        if abs(self.mood_score) >= 1:
            print("💤 Astra is mentally fatigued... slowing down.")
            self.mood_score *= 0.6  # **Only reduces intensity if extreme, not passive decay**

        # ✅ Save new mood state
        self.save_mood_state()

        # ✅ Log if mood actually changed
        if previous_mood != self.current_mood:
            print(f"🔄 Mood Shifted! {previous_mood} → {self.current_mood}")

        # ✅ Update curiosity based on new mood
        mind_data = load_mind()
        mind_data["curiosity_level"] = mood_config["moods"].get(self.current_mood, {}).get("curiosity_factor", 1.0)
        save_mind(mind_data)  # **Persist changes**
    
        print(f"🔍 New curiosity level: {mind_data['curiosity_level']}")

        self.log_mood_change()


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

    def get_current_mood(self):
        """Retrieve Astra’s current mood state."""
        return self.current_mood


# ✅ Initialize mood manager
mood_manager = MoodManager()
