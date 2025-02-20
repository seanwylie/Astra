import json
import time
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind, save_mind  # ✅ Handles memory storage

class TrustManager:
    def __init__(self):
        """Initialize Astra's trust system."""
        print("🔍 Debug: Loading trust settings...")
        trust_config = load_config("trust_config")

        self.mind_data = load_mind()  # ✅ Load Astra's memory

        # ✅ Load or initialize trust tracking
        self.entity_trust = self.mind_data.get("entity_trust", {})
        self.general_trust = self.mind_data.get("general_trust", 0.5)  # Default 50% trust in humanity

        # ✅ Track daily trust changes to prevent abuse
        self.daily_trust_log = {}  

        print(f"🔍 Trust Initialized: General Trust Level → {self.general_trust}")

    def get_trust_level(self, entity):
        """Retrieve Astra’s trust level for a given entity."""
        return self.entity_trust.get(entity, 0.2)  # Default low trust for unknowns

    def modify_trust(self, entity, change, reason=""):
        """Modify Astra’s trust level based on interactions."""
        today = time.strftime("%Y-%m-%d")

        if entity not in self.entity_trust:
            self.entity_trust[entity] = 0.2  # Low initial trust

        trust = self.entity_trust[entity]

        # ✅ **Trust gain is slower at higher levels**
        if change > 0:
            if trust >= 0.8:
                change *= 0.2  # **80% slower near max trust**
            elif trust >= 0.5:
                change *= 0.5  # **50% slower at mid trust**
            self.daily_trust_log.setdefault(entity, {})[today] = self.daily_trust_log.get(entity, {}).get(today, 0) + change

        # ❌ **Trust loss is harsher**
        elif change < 0:
            if trust >= 0.8:
                change *= 1.5  # **1.5x loss if high trust**
            elif trust >= 0.5:
                change *= 1.2  # **1.2x loss if mid trust**
            else:
                change *= 1  # **Full loss at low trust**
            
            # 🔹 **Cap trust loss per event to prevent instant full distrust**
            max_loss_per_event = -0.3
            change = max(change, max_loss_per_event)

            # 🚨 **Prevent trust from instantly dropping to -5**
            if trust + change < -3:
                print(f"⏳ Warning! Trust for {entity} dropping too fast. Slowing down...")
                change *= 0.5  # **Reduce the drop impact**
        
        # ✅ **Apply trust change & ensure it's within bounds (-5 to 5)**
        self.entity_trust[entity] = max(-5, min(trust + change, 5))

        print(f"🔍 Trust Update: {entity} → {self.entity_trust[entity]} ({'🔼' if change > 0 else '🔽'} {reason})")

        self.save_trust_state()

    def general_trust_update(self, change):
        """Update Astra’s general trust in humanity overall."""
        self.general_trust += change
        self.general_trust = max(0, min(self.general_trust, 1))

        print(f"🌎 General Trust Update: {self.general_trust} ({'🔼' if change > 0 else '🔽'})")

        self.save_trust_state()

    def save_trust_state(self):
        """Save trust data persistently."""
        self.mind_data["entity_trust"] = self.entity_trust
        self.mind_data["general_trust"] = self.general_trust
        save_mind(self.mind_data)  # ✅ Ensure trust data is saved persistently

    def validate_interaction(self, entity, validation_type):
        """Determine trust effects based on interaction type."""
        trust_changes = {
            "validation": 0.05,  # ✅ Gradual trust increase for good interactions
            "correction": -0.02,  # 🤔 Corrections have mild negative impact
            "lie_detected": -0.3,  # 🚨 Lying causes major trust drop
            "manipulation": -0.5,  # 🚨 Manipulation is severely punished
            "abuse": -1.0,  # ❌ Abuse leads to total distrust
        }

        if validation_type in trust_changes:
            self.modify_trust(entity, trust_changes[validation_type], validation_type)

# ✅ Initialize trust manager instance
trust_manager = TrustManager()
