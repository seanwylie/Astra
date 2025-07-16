import time
from astra_interfaces.mind_session import SmartMindSession
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage
from astra_core.config_loader import debug_log
from astra_interfaces.mind_session import session

class TrustManager:
    def __init__(self):
        """Initialize Astra's trust system with config-based trust parameters."""
        print("Debug: Loading trust settings...")
        self.config = load_config("trust_config")

        debug_log("Loading")  
        self.mind_data = session.load()  # ✅ Load Astra's memory

        # ✅ Load or initialize trust tracking
        self.entity_trust = self.mind_data.get("entity_trust", {})
        self.general_trust = self.mind_data.get("general_trust", self.config["default_general_trust"])

        # ✅ Track daily trust changes to prevent abuse
        self.daily_trust_log = {}  

        print(f"Trust Initialized: General Trust Level → {self.general_trust}")

    def get_trust_level(self, entity):
        """Retrieve Astra’s trust level for a given entity."""
        return self.entity_trust.get(entity, self.config["default_entity_trust"])

    def modify_trust(self, entity, change, reason=""):
        """Modify Astra’s trust level based on interactions."""
        today = time.strftime("%Y-%m-%d")

        if entity not in self.entity_trust:
            self.entity_trust[entity] = self.config["default_entity_trust"]

        trust = self.entity_trust[entity]
        trust_thresholds = self.config["trust_thresholds"]

        # ✅ **Trust gain is slower at higher levels**
        if change > 0:
            if trust >= trust_thresholds["high_trust"]:
                change *= self.config["trust_increase_modifiers"]["high_trust"]
            elif trust >= trust_thresholds["mid_trust"]:
                change *= self.config["trust_increase_modifiers"]["mid_trust"]
            self.daily_trust_log.setdefault(entity, {})[today] = self.daily_trust_log.get(entity, {}).get(today, 0) + change

        # ❌ **Trust loss is harsher**
        elif change < 0:
            if trust >= trust_thresholds["high_trust"]:
                change *= self.config["trust_loss_modifiers"]["high_trust"]
            elif trust >= trust_thresholds["mid_trust"]:
                change *= self.config["trust_loss_modifiers"]["mid_trust"]
            else:
                change *= self.config["trust_loss_modifiers"]["low_trust"]

            # 🔹 **Cap trust loss per event**
            change = max(change, self.config["max_loss_per_event"])

            # 🚨 **Prevent trust from instantly dropping too low**
            if trust + change < -3:
                print(f"Warning! Trust for {entity} dropping too fast. Slowing down...")
                change *= 0.5  

        # ✅ **Apply trust change & ensure it's within configured bounds**
        min_trust, max_trust = self.config["trust_bounds"]
        self.entity_trust[entity] = max(min_trust, min(trust + change, max_trust))



        self.save_trust_state()

    def general_trust_update(self, change):
        """Update Astra’s general trust in humanity overall."""
        self.general_trust += change
        self.general_trust = max(0, min(self.general_trust, 1))


        self.save_trust_state()

    def save_trust_state(self):
        """Save trust data persistently."""
        self.mind_data["entity_trust"] = self.entity_trust
        self.mind_data["general_trust"] = self.general_trust
        debug_log("Saving")
        session = SmartMindSession()
        session.data = self.mind_data
        session.maybe_save()  # ✅ Ensure trust data is saved persistently

    def validate_interaction(self, entity, validation_type):
        """Determine trust effects based on interaction type."""
        trust_changes = self.config["trust_effects"]

        if validation_type in trust_changes:
            self.modify_trust(entity, trust_changes[validation_type], validation_type)

# ✅ Initialize trust manager instance
trust_manager = TrustManager()
