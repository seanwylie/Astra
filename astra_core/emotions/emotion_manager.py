import json
import os
import time
from astra_interfaces.influence import save_mind, load_mind

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/emotion_config.json")

class EmotionManager:
    def __init__(self):
        self.last_update_time = time.time()  # ✅ Add this line first
        self.emotions = {}
        self.load_emotions()

        # Merge emotional intensities from memory
        mind_data = load_mind()
        saved = mind_data.get("emotional_state", {})
        for emotion, state in self.emotions.items():
            if emotion in saved:
                state["intensity"] = saved[emotion]
        
        print("🧠 Emotional state loaded:", self.get_emotional_state())


    def save_emotions_to_memory(self):
        mind_data = load_mind()
        mind_data["emotional_state"] = self.get_emotional_state()
        save_mind(mind_data)

    def load_emotions(self):
        """Load emotions from the config file."""
        try:
            with open(CONFIG_PATH, "r") as file:
                config = json.load(file)
                self.emotions = {
                    emotion: {
                        "intensity": data["intensity"],
                        "decay_rate": data["decay_rate"],
                        "triggers": data["triggers"],
                        "relationships": data.get("relationships", {}),
                        "long_term_effect": data.get("long_term_effect", ""),
                    }
                    for emotion, data in config["emotions"].items()
                }
        except Exception as e:
            print(f"Error loading emotion config: {e}")

    def normalize_emotions(self):
        for emotion, data in self.emotions.items():
            if data["intensity"] > 100:
                data["intensity"] = 100

    def update_emotions(self):
        """Decay emotions over time and apply inter-emotion relationships with stronger decay at high levels."""
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time

        # Step 1: Apply Stronger Adaptive Decay
        for emotion, data in self.emotions.items():
            intensity = data["intensity"]

            # Stronger decay when intensity is very high
            decay_multiplier = 1 + (intensity / 50)  # More decay above 50
            decay_amount = (data["decay_rate"] * decay_multiplier) * elapsed_time

            # Prevent emotions from staying maxed
            if intensity > 90:
                decay_amount *= 1.5  # Increase decay further when near max

            data["intensity"] = max(0, intensity - decay_amount)

        # Step 2: Apply Relationships with Less Reinforcement at High Levels
        for emotion, data in self.emotions.items():
            for related_emotion, impact in data["relationships"].items():
                if related_emotion in self.emotions:
                    relationship_effect = impact * elapsed_time

                    # Reduce relationship impact if the emotion is already high
                    intensity_factor = max(0, (100 - self.emotions[related_emotion]["intensity"]) / 100)
                    relationship_effect *= intensity_factor ** 2  # Stronger damping at high levels

                    self.emotions[related_emotion]["intensity"] += relationship_effect
                    self.emotions[related_emotion]["intensity"] = max(0, min(100, self.emotions[related_emotion]["intensity"]))

        # ✅ Step 3: Normalize Emotion Intensities
        for emotion, data in self.emotions.items():
            if data["intensity"] > 100:
                data["intensity"] = 100

        self.last_update_time = current_time
        self.save_emotions_to_memory()



    def apply_trigger(self, emotion, trigger):
        """Adjust an emotion based on a trigger event."""
        if emotion in self.emotions and trigger in self.emotions[emotion]["triggers"]:
            self.emotions[emotion]["intensity"] += self.emotions[emotion]["triggers"][trigger]
            self.emotions[emotion]["intensity"] = max(0, self.emotions[emotion]["intensity"])  # No negative intensities

    def get_emotional_state(self):
        """Return a snapshot of Astra's current emotions."""
        return {
            emotion: round(data["intensity"], 2)
            for emotion, data in sorted(self.emotions.items(), key=lambda x: x[1]["intensity"], reverse=True)
            if data["intensity"] > 0
        }

    def get_dominant_emotion(self):
        """Return the most dominant emotion, with positive-weighted conflict resolution."""
        active_emotions = self.get_emotional_state()
        if not active_emotions:
            return "curiosity"

        sorted_emotions = sorted(active_emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotion, top_intensity = sorted_emotions[0]

        # Special override: obsession if it's overwhelmingly strong
        if "obsession" in active_emotions and active_emotions["obsession"] > 120:
            return "obsession"

        # Define emotional conflicts (antagonists)
        opposites = {
            "hate": "love",
            "anger": "compassion",
            "grief": "hope",
            "resentment": "forgiveness",
            "uncertainty": "confidence"
        }

        # Conflict logic: if the opposite of a negative emotion is higher, prefer the positive one
        for neg, pos in opposites.items():
            if neg in active_emotions and pos in active_emotions:
                if active_emotions[pos] > active_emotions[neg] + 2:
                    return pos

        # Override hate dominance unless it is *truly* the highest
        if "hate" in active_emotions and active_emotions["hate"] > 90:
            if top_emotion != "hate" and top_intensity > active_emotions["hate"]:
                return top_emotion
            return "hate"

        return top_emotion



    def modify_emotion(self, emotion, intensity_change):
        """Manually modify an emotion's intensity (for external adjustments)."""
        if emotion in self.emotions:
            self.emotions[emotion]["intensity"] += intensity_change
            self.emotions[emotion]["intensity"] = max(0, self.emotions[emotion]["intensity"])


# Example usage
if __name__ == "__main__":
    manager = EmotionManager()
    print("Initial state:", manager.get_emotional_state())

    manager.apply_trigger("curiosity", "new_information")
    print("After trigger:", manager.get_emotional_state())

    time.sleep(2)  # Simulate time passing
    manager.update_emotions()
    print("After decay:", manager.get_emotional_state())

    print("Dominant emotion:", manager.get_dominant_emotion())
