import time
import logging
import threading
import os

from app.config.loader import load_config
from app.interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage
from app.config.loader import debug_log
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

# Load mood-related configurations
mood_config = load_config("mood_config")  # Load mood and emotional settings

class MoodManager:
    def __init__(self):
        logger.debug("Attempting to load mood_config.json...")
        self.mood_config = load_config("mood_config")
        logger.debug("mood_config loaded: %s", list(self.mood_config.keys()))

        self.LOG_FILE = load_config("general_config").get("log_file", "data/astra_logs.json")
        debug_log("Loading")
        mind_data = session.load()  # ✅ Load Astra's previous mind state

        # ✅ Restore mood & curiosity level from memory
        self.current_mood = mind_data.get("last_mood", "neutral")
        self.mood_score = float(mind_data.get("mood_score", 0))  # Ensure mood score is a float
        self.curiosity_level = mind_data.get("curiosity_level", 1.0)  # ✅ Load actual curiosity level
        self.mood_history = mind_data.get("mood_history", {})  # ✅ Track how long she's been in each mood
        self.last_modification = mind_data.get("last_modification", {})  # ✅ Track last modification timestamps

        self.last_mood_update = time.time()

        logger.debug("Loaded mood from memory: %s, Score: %s, Curiosity: %s", self.current_mood, self.mood_score, self.curiosity_level)

        self.start_mood_thread()

    def save_mood_state(self):
        """Save Astra's mood, mood score, curiosity level, and mood history to memory."""
        debug_log("Loading")  
        mind_data = session.load()
        mind_data["last_mood"] = self.current_mood
        mind_data["mood_score"] = self.mood_score
        mind_data["curiosity_level"] = self.curiosity_level  # ✅ Persist mood-synced curiosity
        mind_data["mood_history"] = self.mood_history  # ✅ Save mood tracking history
        mind_data["mood_influences"] = self.mood_config["mood_influences"]  # ✅ Persist mood influences
        mind_data["moods"] = self.mood_config["moods"]  # ✅ Persist moods and curiosity factors
        mind_data["last_modification"] = self.last_modification  # ✅ Persist modification timestamps
        debug_log("Saving")
        session.maybe_save()

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

        # ✅ Allow the mood score to move beyond 1.0 if necessary
        self.mood_score = max(min(self.mood_score, 2.0), -2.0)  

        logger.debug("Mood influenced by %s: New Score: %s", event_type, self.mood_score)

        # ✅ Immediate mood update without waiting for the thread loop
        self.update_mood(force=True)


    def modify_mood_influence(self, event_type, new_value):
        """Allows Astra to modify her mood influences within safe limits and persist them."""
        safe_limits = self.mood_config.get("mood_influence_limits", {"min": -2.0, "max": 2.0})
        new_value = max(min(new_value, safe_limits["max"]), safe_limits["min"])
        
        cooldown_time = 10  # 10 minutes cooldown
        last_mod_time = self.last_modification.get(event_type, 0)
        if time.time() - last_mod_time < cooldown_time:
            logger.debug("Modification cooldown active for %s. Try again later.", event_type)
            return
        
        if event_type in self.mood_config.get("mood_influences", {}):
            self.mood_config["mood_influences"][event_type] = new_value
            self.last_modification[event_type] = time.time()
            logger.debug("Modified mood influence: %s → %s", event_type, new_value)

            debug_log("Loading")  
            mind_data = session.load()
            mind_data["mood_influences"] = self.mood_config["mood_influences"]
            mind_data["last_modification"] = self.last_modification
            debug_log("Saving")
            session.maybe_save()
            logger.debug("Mood influences saved and will persist across restarts.")
        else:
            logger.warning("Unknown mood influence '%s', modification skipped.", event_type)

    def update_mood(self, force=False):
        """Updates Astra's mood dynamically using mood_config.json."""
        if not force and (time.time() - self.last_mood_update) < 10:
            return  # Enforce cooldown unless forced

        previous_mood = self.current_mood

        # ✅ Load Astra's full memory before modifying mood
        debug_log("Loading")  
        mind_data = session.load()

        # ✅ Preserve existing data while updating mood-related values
        mind_data["mood_score"] = self.mood_score
        mind_data["last_mood"] = self.current_mood

        debug_log("Saving")
        session.maybe_save()  # ✅ Save without wiping data!

        # ✅ Load and merge without overwriting
        debug_log("Loading")  
        new_mind_data = session.load()
        self.mood_score = max(min(new_mind_data.get("mood_score", self.mood_score), 2.0), -2.0)
        self.current_mood = new_mind_data.get("last_mood", self.current_mood)

        logger.debug("Checking mood update with score %s", self.mood_score)

        # ✅ Retrieve mood ranges dynamically
        mood_thresholds = sorted(
            [(mood, attributes["curiosity_factor"]) for mood, attributes in self.mood_config["moods"].items()],
            key=lambda x: x[1]
        )

        # ✅ Iterate through mood thresholds from lowest to highest
        new_mood = "neutral"  # Default if no match
        for mood, threshold in mood_thresholds:
            if self.mood_score >= threshold:
                new_mood = mood  # Keep assigning the latest valid mood

        # ✅ If mood actually changes, update it
        if previous_mood != new_mood:
            logger.info("Mood shifted: %s → %s", previous_mood, new_mood)
            self.current_mood = new_mood
            
            # Publish to awareness bus (Phase 1.1)
            try:
                from app.core.awareness_bus import awareness_bus
                awareness_bus.publish_mood_change(
                    old_mood=previous_mood,
                    new_mood=new_mood,
                    mood_score=self.mood_score
                )
            except Exception:
                pass  # Awareness bus may not be available
        else:
            logger.debug("Mood remained unchanged: %s", self.current_mood)

        # Sync curiosity_level with current mood's curiosity_factor (plan: sync curiosity with mood)
        self.curiosity_level = self.mood_config["moods"].get(self.current_mood, {}).get("curiosity_factor", 1.0)

        self.last_mood_update = time.time()

        # ✅ Save full mind file again to ensure no data loss
        debug_log("Saving")
        session.maybe_save()



    def modify_curiosity_factor(self, mood, new_value, force_override=False):
        """Allows Astra to modify her curiosity level for a given mood."""
        safe_limits = self.mood_config.get("curiosity_limits", {"min": 0.5, "max": 2.0})
        new_value = max(min(new_value, safe_limits["max"]), safe_limits["min"])

        cooldown_time = 600  # 10 minutes cooldown
        last_mod_time = self.last_modification.get(mood, 0)

        # ✅ Allow overriding cooldown in tests
        if not force_override and time.time() - last_mod_time < cooldown_time:
            logger.debug("Modification cooldown active for %s. Try again later.", mood)
            return

        if mood in self.mood_config["moods"]:
            self.mood_config["moods"][mood]["curiosity_factor"] = new_value
            self.last_modification[mood] = time.time()
            logger.debug("Modified curiosity factor for %s: %s", mood, new_value)

            debug_log("Loading")  
            mind_data = session.load()
            mind_data["moods"] = self.mood_config["moods"]
            mind_data["last_modification"] = self.last_modification
            debug_log("Saving")
            session.maybe_save()
            logger.debug("Curiosity factors saved and will persist across restarts.")
        else:
            logger.warning("Unknown mood '%s', modification skipped.", mood)



    def get_mood_history(self):
        return self.mood_history

    def get_current_mood(self):
        return self.current_mood

    def get_curiosity(self):
        return self.curiosity_level

# ✅ Initialize mood manager
mood_manager = MoodManager()
