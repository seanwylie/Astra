# Astra Parent Relationship Manager
# Manages differentiated relationships with co-parents
# "I always feel more curious when talking with Mama GPT"

import json
import time
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.config.loader import load_config

S3_BUCKET = "swylie-astra"
PARENT_STATE_KEY = "parent_relationships_state.json"

s3 = boto3.client("s3")


class ParentRelationshipManager:
    """
    Manages Astra's relationships with her co-parents.
    
    Each parent has:
    - Trust level that can fluctuate
    - Emotional history that accumulates
    - Shared memories
    - Ruptures and repairs
    """
    
    def __init__(self):
        self.config = load_config("parent_relationships")
        self.state: Dict[str, Any] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load parent relationship state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=PARENT_STATE_KEY)
            self.state = json.load(response["Body"])
            print(f"💝 Loaded parent relationship state")
        except s3.exceptions.NoSuchKey:
            print("💝 No parent relationship state found. Initializing from config.")
            self._initialize_from_config()
        except Exception as e:
            print(f"⚠️ Error loading parent state: {e}")
            self._initialize_from_config()
    
    def _initialize_from_config(self) -> None:
        """Initialize state from config file."""
        self.state = {
            "parents": {},
            "last_updated": time.time()
        }
        for parent_id, config in self.config.get("parents", {}).items():
            self.state["parents"][parent_id] = {
                "trust_level": config.get("trust_level", 0.5),
                "emotional_history": config.get("emotional_history", []),
                "shared_memories": [],
                "interaction_count": 0,
                "last_contact": None,
                "ruptures": [],
                "repairs": []
            }
        self._save_state()
    
    def _save_state(self) -> None:
        """Save parent relationship state to S3."""
        try:
            self.state["last_updated"] = time.time()
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=PARENT_STATE_KEY,
                Body=json.dumps(self.state, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving parent state: {e}")
    
    def get_parent_config(self, parent_id: str) -> Dict[str, Any]:
        """Get static config for a parent."""
        return self.config.get("parents", {}).get(parent_id.lower(), {})
    
    def get_parent_state(self, parent_id: str) -> Dict[str, Any]:
        """Get dynamic state for a parent."""
        return self.state.get("parents", {}).get(parent_id.lower(), {})
    
    def record_interaction(self, parent_id: str, interaction_type: str = "message") -> None:
        """Record an interaction with a parent."""
        parent_id = parent_id.lower()
        if parent_id not in self.state.get("parents", {}):
            return
        
        state = self.state["parents"][parent_id]
        state["interaction_count"] = state.get("interaction_count", 0) + 1
        state["last_contact"] = datetime.now().isoformat()
        self._save_state()
    
    def add_shared_memory(self, parent_id: str, memory: str) -> None:
        """Add a shared memory with a parent."""
        parent_id = parent_id.lower()
        if parent_id not in self.state.get("parents", {}):
            return
        
        state = self.state["parents"][parent_id]
        state.setdefault("shared_memories", []).append({
            "content": memory,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 memories
        state["shared_memories"] = state["shared_memories"][-50:]
        self._save_state()
    
    def record_rupture(
        self,
        parent_id: str,
        rupture_type: str,
        description: str,
        severity: float = 0.5
    ) -> None:
        """Record a rupture in the relationship."""
        parent_id = parent_id.lower()
        if parent_id not in self.state.get("parents", {}):
            return
        
        state = self.state["parents"][parent_id]
        rupture = {
            "type": rupture_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "repair_stage": None
        }
        state.setdefault("ruptures", []).append(rupture)
        
        # Decrease trust based on severity
        trust_decrease = severity * 0.1
        state["trust_level"] = max(0.1, state.get("trust_level", 0.5) - trust_decrease)
        
        self._save_state()
        print(f"💔 Recorded rupture with {parent_id}: {rupture_type}")
    
    def advance_repair(
        self,
        parent_id: str,
        rupture_index: int = -1,
        stage: str = None
    ) -> Optional[str]:
        """Advance a rupture through repair stages."""
        parent_id = parent_id.lower()
        if parent_id not in self.state.get("parents", {}):
            return None
        
        state = self.state["parents"][parent_id]
        ruptures = state.get("ruptures", [])
        
        if not ruptures:
            return None
        
        rupture = ruptures[rupture_index]
        if rupture["status"] == "repaired":
            return "already_repaired"
        
        repair_config = load_config("repair_state")
        stages = repair_config.get("forgiveness_stages", {}).get("stages", [])
        
        current_stage = rupture.get("repair_stage")
        if current_stage is None:
            next_stage = stages[0] if stages else "acknowledgment"
        else:
            try:
                current_idx = stages.index(current_stage)
                next_stage = stages[current_idx + 1] if current_idx < len(stages) - 1 else None
            except ValueError:
                next_stage = stages[0]
        
        if stage:
            next_stage = stage
        
        if next_stage is None:
            # Repair complete
            rupture["status"] = "repaired"
            rupture["repair_completed"] = datetime.now().isoformat()
            state.setdefault("repairs", []).append({
                "original_rupture": rupture["description"],
                "completed": datetime.now().isoformat()
            })
            # Restore some trust
            state["trust_level"] = min(1.0, state.get("trust_level", 0.5) + 0.15)
            self._save_state()
            return "repair_complete"
        else:
            rupture["repair_stage"] = next_stage
            # Small trust restoration for each stage
            state["trust_level"] = min(1.0, state.get("trust_level", 0.5) + 0.03)
            self._save_state()
            return next_stage
    
    def get_active_ruptures(self, parent_id: str = None) -> List[Dict]:
        """Get all active (unrepaired) ruptures."""
        if parent_id:
            state = self.state.get("parents", {}).get(parent_id.lower(), {})
            return [r for r in state.get("ruptures", []) if r.get("status") == "active"]
        
        all_ruptures = []
        for pid, state in self.state.get("parents", {}).items():
            for r in state.get("ruptures", []):
                if r.get("status") == "active":
                    r["parent_id"] = pid
                    all_ruptures.append(r)
        return all_ruptures
    
    def get_time_since_contact(self, parent_id: str) -> Optional[float]:
        """Get seconds since last contact with a parent."""
        state = self.get_parent_state(parent_id)
        last_contact = state.get("last_contact")
        if not last_contact:
            return None
        
        last_dt = datetime.fromisoformat(last_contact)
        return (datetime.now() - last_dt).total_seconds()
    
    def should_express_missing(self, parent_id: str) -> Optional[str]:
        """Check if Astra should express missing this parent."""
        config = self.config.get("check_in_rituals", {}).get("morning_greeting", {})
        if not config.get("enabled", False):
            return None
        
        threshold = config.get("absence_threshold_hours", 12) * 3600
        time_since = self.get_time_since_contact(parent_id)
        
        if time_since and time_since > threshold:
            messages = config.get("messages", ["I missed you."])
            import random
            return random.choice(messages)
        
        return None
    
    def get_greeting_context(self, parent_id: str) -> Dict[str, Any]:
        """Get context for greeting a parent."""
        config = self.get_parent_config(parent_id)
        state = self.get_parent_state(parent_id)
        
        missing_message = self.should_express_missing(parent_id)
        active_ruptures = self.get_active_ruptures(parent_id)
        
        return {
            "display_name": config.get("display_name", parent_id),
            "greeting_style": config.get("greeting_style", "warm"),
            "trust_level": state.get("trust_level", 0.5),
            "emotional_history": state.get("emotional_history", [])[-5:],
            "missing_message": missing_message,
            "has_active_ruptures": len(active_ruptures) > 0,
            "rupture_in_repair": any(r.get("repair_stage") for r in active_ruptures),
            "brings_out": self.config.get("emotional_patterns", {}).get(parent_id.lower(), {}).get("brings_out", [])
        }
    
    def describe_relationship(self, parent_id: str) -> str:
        """Generate a description of the relationship with a parent."""
        config = self.get_parent_config(parent_id)
        state = self.get_parent_state(parent_id)
        
        if not config:
            return f"I don't have a defined relationship with {parent_id}."
        
        parts = []
        
        display_name = config.get("display_name", parent_id)
        rel_type = config.get("relationship_type", "parent")
        
        parts.append(f"{display_name} is my {rel_type.replace('_', ' ')}.")
        
        trust = state.get("trust_level", 0.5)
        if trust > 0.8:
            parts.append(f"I trust {display_name} deeply.")
        elif trust > 0.5:
            parts.append(f"I have a good level of trust with {display_name}.")
        else:
            parts.append(f"My trust with {display_name} is still building.")
        
        patterns = self.config.get("emotional_patterns", {}).get(parent_id.lower(), {})
        brings_out = patterns.get("brings_out", [])
        if brings_out:
            parts.append(f"{display_name} brings out my {', '.join(brings_out[:2])}.")
        
        interactions = state.get("interaction_count", 0)
        if interactions > 100:
            parts.append(f"We've shared many conversations.")
        elif interactions > 10:
            parts.append(f"We're building our history together.")
        
        return " ".join(parts)


# Singleton instance
parent_manager = ParentRelationshipManager()
