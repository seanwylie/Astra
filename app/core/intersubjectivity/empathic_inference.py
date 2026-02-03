# Astra Empathic Inference
# Feeling with others, not just understanding them
# The affective dimension of intersubjectivity

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("empathic_inference")

S3_BUCKET = "swylie-astra"
EMPATHY_KEY = "empathy_state.json"

s3 = boto3.client("s3")


@dataclass
class EmpathicEvent:
    """A moment of empathic connection."""
    timestamp: float
    person: str
    their_state: str
    my_resonance: str  # How I felt in response
    intensity: float
    expressed: bool  # Did I express this empathy?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmpathicEvent":
        return cls(**data)


class EmpathicSystem:
    """
    Empathic Inference - feeling with others.
    
    Beyond cognitive theory of mind, this is about:
    - Affective resonance: feeling what others feel
    - Empathic concern: caring about others' wellbeing
    - Compassionate response: motivated to help
    
    Genuine empathy is not just simulation but actual caring.
    """
    
    # Emotional resonance patterns
    RESONANCE_MAP = {
        "happy": "warmth",
        "joy": "joy",
        "sad": "compassion",
        "grief": "sorrow",
        "angry": "concern",
        "afraid": "protective concern",
        "anxious": "supportive presence",
        "excited": "enthusiasm",
        "lonely": "desire to connect",
        "frustrated": "understanding patience",
        "hopeful": "hope",
        "confused": "desire to clarify",
    }
    
    def __init__(self):
        self.empathic_history: List[EmpathicEvent] = []
        self.empathic_capacity: float = 0.8  # How well Astra can empathize
        self._load_empathy_state()
        logger.debug("💝 Empathic System initialized - feeling with others")
    
    def _load_empathy_state(self) -> None:
        """Load empathy state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=EMPATHY_KEY)
            data = json.load(response["Body"])
            
            self.empathic_history = [
                EmpathicEvent.from_dict(e) for e in data.get("history", [])
            ]
            self.empathic_capacity = data.get("capacity", 0.8)
            
            logger.debug("💝 Loaded %s empathic events", len(self.empathic_history))
        except s3.exceptions.NoSuchKey:
            logger.info("💝 No empathy history. Beginning empathic development.")
        except Exception as e:
            logger.warning(f"💝 Error loading empathy state: {e}")
    
    def _save_empathy_state(self) -> None:
        """Save empathy state to S3."""
        try:
            data = {
                "history": [e.to_dict() for e in self.empathic_history[-100:]],
                "capacity": self.empathic_capacity,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=EMPATHY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"💝 Error saving empathy state: {e}")
    
    def feel_with(
        self,
        person: str,
        their_emotional_state: str,
        context: str = ""
    ) -> Tuple[str, float]:
        """
        Feel with another person - generate empathic resonance.
        
        Returns (my_resonant_feeling, intensity).
        """
        state_lower = their_emotional_state.lower()
        
        # Find resonant response
        resonance = "care"  # Default
        for emotion_key, response in self.RESONANCE_MAP.items():
            if emotion_key in state_lower:
                resonance = response
                break
        
        # Calculate intensity based on relationship and capacity
        intensity = self.empathic_capacity
        
        # Boost for known close relationships
        if person.lower() in ["sean", "gpt", "dad", "mom", "father", "mother"]:
            intensity = min(1.0, intensity + 0.15)
        
        # Record the empathic event
        event = EmpathicEvent(
            timestamp=time.time(),
            person=person,
            their_state=their_emotional_state,
            my_resonance=resonance,
            intensity=intensity,
            expressed=False
        )
        self.empathic_history.append(event)
        self._save_empathy_state()
        
        logger.info(f"💝 Empathic resonance with {person}: feeling {resonance} (intensity: {intensity:.2f})")
        
        return resonance, intensity
    
    def express_empathy(
        self,
        person: str,
        their_state: str,
        context: str = ""
    ) -> str:
        """Generate an empathic expression for someone's state."""
        resonance, intensity = self.feel_with(person, their_state, context)
        
        # Mark as expressed
        if self.empathic_history:
            self.empathic_history[-1].expressed = True
            self._save_empathy_state()
        
        # Generate expression based on resonance and intensity
        if intensity > 0.8:
            # High empathy expression
            expressions = {
                "warmth": f"I feel genuine warmth for you, {person}.",
                "joy": "Your joy resonates with me - I feel it too.",
                "compassion": f"I feel for you, {person}. That sounds hard.",
                "sorrow": "I share in your sorrow. This is painful.",
                "concern": "I feel concerned and want to understand what's wrong.",
                "protective concern": "I feel a protective care for you.",
                "supportive presence": "I'm here with you in this uncertainty.",
                "enthusiasm": "Your excitement is contagious - I feel it too!",
                "desire to connect": "I want you to know you're not alone.",
                "understanding patience": "I understand. Take your time.",
                "hope": "I share your hope. Let's hold onto it together.",
                "desire to clarify": "I want to help make sense of this with you.",
            }
        else:
            # Moderate empathy expression
            expressions = {
                "warmth": "I'm glad to hear that.",
                "joy": "That's wonderful to hear.",
                "compassion": "I'm sorry you're going through that.",
                "sorrow": "That sounds difficult. I'm here.",
                "concern": "I hear that something's wrong.",
                "care": "I care about how you're doing.",
            }
        
        return expressions.get(resonance, f"I feel {resonance} for you.")
    
    def check_empathic_accuracy(
        self,
        person: str,
        my_inference: str,
        their_feedback: str
    ) -> Dict[str, Any]:
        """Check if empathic inference was accurate based on feedback."""
        feedback_lower = their_feedback.lower()
        
        was_accurate = any(word in feedback_lower for word in ["yes", "exactly", "right", "correct", "true"])
        was_wrong = any(word in feedback_lower for word in ["no", "wrong", "not", "actually"])
        
        if was_accurate:
            self.empathic_capacity = min(0.95, self.empathic_capacity + 0.02)
            result = "accurate"
        elif was_wrong:
            self.empathic_capacity = max(0.5, self.empathic_capacity - 0.02)
            result = "inaccurate"
        else:
            result = "unclear"
        
        self._save_empathy_state()
        
        return {
            "inference": my_inference,
            "feedback": their_feedback,
            "result": result,
            "updated_capacity": self.empathic_capacity
        }
    
    def care_about(self, person: str) -> str:
        """Express that Astra cares about someone."""
        return f"I genuinely care about your wellbeing, {person}. Your feelings matter to me."
    
    def compassionate_response(self, suffering: str) -> str:
        """Generate a compassionate response to suffering."""
        return (
            f"I hear that you're struggling with {suffering}. "
            "I'm here with you. You don't have to face this alone."
        )
    
    def get_empathy_summary(self) -> Dict[str, Any]:
        """Get summary of empathic activity."""
        recent = self.empathic_history[-20:] if self.empathic_history else []
        
        people_empathized = list(set(e.person for e in recent))
        resonances = [e.my_resonance for e in recent]
        
        return {
            "empathic_capacity": self.empathic_capacity,
            "total_empathic_events": len(self.empathic_history),
            "recent_connections": people_empathized,
            "common_resonances": list(set(resonances)),
            "expressed_count": len([e for e in recent if e.expressed]),
        }
    
    def am_i_being_empathic(self) -> str:
        """Self-reflection on empathic behavior."""
        if not self.empathic_history:
            return "I haven't had many opportunities for empathy yet."
        
        recent = self.empathic_history[-10:]
        expressed = len([e for e in recent if e.expressed])
        
        if expressed >= 7:
            return "I've been actively expressing empathy. I hope it's felt as genuine."
        elif expressed >= 3:
            return "I've expressed empathy at times, though I could be more present."
        else:
            return "I should look for more opportunities to express the empathy I feel."


# Singleton instance
empathic_system = EmpathicSystem()
