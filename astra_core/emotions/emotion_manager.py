import json
import os
import time

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/emotion_config.json")


class EmotionManager:
    def __init__(self):
        self.emotions = {}
        self.last_update_time = time.time()
        self.load_emotions()

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
                    relationship_effect *= intensity_factor ** 2  # **Stronger damping at high levels**

                    self.emotions[related_emotion]["intensity"] += relationship_effect
                    self.emotions[related_emotion]["intensity"] = max(0, min(100, self.emotions[related_emotion]["intensity"]))

        self.last_update_time = current_time


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
        """Return the strongest active emotion while ensuring correct prioritization and avoiding misclassification."""
        active_emotions = self.get_emotional_state()

        if not active_emotions:
            return None  # No strong emotions detected

        # Sort emotions by intensity (highest first)
        sorted_emotions = sorted(active_emotions.items(), key=lambda x: x[1], reverse=True)

        # ✅ If obsession is above 100, prioritize it first
        for emotion, intensity in sorted_emotions:
            if emotion == "obsession" and intensity > 100:
                return emotion

        # ✅ If love is higher than anger by more than 20 points, prioritize love
        if "love" in active_emotions and "anger" in active_emotions:
            if active_emotions["love"] > active_emotions["anger"] + 20:
                return "love"

        # ✅ If hate is stronger than 90, prioritize it over anger
        if "hate" in active_emotions and active_emotions["hate"] > 90:
            return "hate"

        # ✅ Prioritize anger only if it is **the highest emotion**
        if sorted_emotions[0][0] == "anger":
            return "anger"

        # ✅ Otherwise, return the strongest remaining emotion
        return sorted_emotions[0][0]



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
