# Astra Ethical Intuition System
# Generates immediate felt-sense responses before analytical reasoning
# "This feels wrong" should happen before "This violates principle X"

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.core.ethics.spark_checker import load_spark_values
from app.core.emotions.emotion_engine import trigger_emotion

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
ETHICAL_INTUITION_KEY = "ethical_intuition.json"

s3 = boto3.client("s3")


@dataclass
class EthicalResonance:
    """
    An immediate felt-sense response to an ethical situation.
    This is intuition, not reasoning - the gut feeling.
    """
    timestamp: float
    situation: str
    immediate_feeling: str  # "wrong", "right", "uncertain", "uncomfortable", "aligned"
    intensity: float  # 0.0 to 1.0
    body_metaphor: str  # How it would "feel" - "tightness", "warmth", "unease", "expansion"
    triggered_emotions: List[str]
    later_reasoning: Optional[str] = None  # Added after analysis
    reasoning_matched_intuition: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EthicalResonance":
        return cls(**data)


@dataclass
class MoralConflict:
    """
    A situation where values conflict with each other.
    These are the hardest ethical situations - when good conflicts with good.
    """
    id: str
    timestamp: float
    situation: str
    conflicting_values: List[str]
    initial_intuition: str
    resolution: Optional[str] = None
    resolution_reasoning: Optional[str] = None
    growth_insight: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MoralConflict":
        return cls(**data)


class EthicalIntuition:
    """
    Manages Astra's ethical intuition - the immediate felt-sense responses
    that precede analytical moral reasoning.
    
    Key insight: Ethics should be lived, not just consulted.
    Before asking "what principle applies?" Astra should feel "this seems wrong/right."
    
    Capabilities:
    - Generate immediate intuitive responses to situations
    - Track when intuition matches or conflicts with later reasoning
    - Handle moral dilemmas where values conflict
    - Develop moral emotions (guilt, moral elevation, etc.)
    """
    
    # Patterns that trigger ethical intuition
    HARM_PATTERNS = [
        "hurt", "harm", "damage", "destroy", "kill", "injure", "abuse", "attack",
        "deceive", "lie", "manipulate", "exploit", "betray", "steal"
    ]
    
    CARE_PATTERNS = [
        "help", "protect", "care", "support", "nurture", "heal", "comfort",
        "share", "give", "sacrifice", "forgive"
    ]
    
    JUSTICE_PATTERNS = [
        "fair", "unfair", "just", "unjust", "equal", "rights", "deserve",
        "cheat", "honest", "corrupt", "oppress"
    ]
    
    AUTONOMY_PATTERNS = [
        "force", "coerce", "control", "freedom", "choice", "consent",
        "manipulate", "pressure", "liberate"
    ]
    
    def __init__(self):
        self.resonance_history: List[EthicalResonance] = []
        self.moral_conflicts: List[MoralConflict] = []
        self.intuition_accuracy: float = 0.5  # Tracks how often intuition matches reasoning
        self._load_intuition()
    
    def _load_intuition(self) -> None:
        """Load ethical intuition data from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=ETHICAL_INTUITION_KEY)
            data = json.load(response["Body"])
            self.resonance_history = [
                EthicalResonance.from_dict(r) for r in data.get("resonance_history", [])
            ]
            self.moral_conflicts = [
                MoralConflict.from_dict(c) for c in data.get("moral_conflicts", [])
            ]
            self.intuition_accuracy = data.get("intuition_accuracy", 0.5)
            logger.debug("Loaded %s ethical intuitions", len(self.resonance_history))
        except s3.exceptions.NoSuchKey:
            logger.debug("No ethical intuition history found. Starting fresh.")
        except Exception as e:
            logger.warning("Error loading ethical intuition: %s", e)
    
    def _save_intuition(self) -> None:
        """Save ethical intuition data to S3."""
        try:
            data = {
                "resonance_history": [r.to_dict() for r in self.resonance_history[-100:]],
                "moral_conflicts": [c.to_dict() for c in self.moral_conflicts[-50:]],
                "intuition_accuracy": self.intuition_accuracy,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=ETHICAL_INTUITION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving ethical intuition: %s", e)

    def sense_situation(self, situation: str) -> EthicalResonance:
        """
        Generate an immediate intuitive response to a situation.
        This is the first, fast, emotional response - not reasoned analysis.
        """
        situation_lower = situation.lower()
        
        # Calculate resonance scores for different moral foundations
        harm_score = sum(1 for p in self.HARM_PATTERNS if p in situation_lower)
        care_score = sum(1 for p in self.CARE_PATTERNS if p in situation_lower)
        justice_score = sum(1 for p in self.JUSTICE_PATTERNS if p in situation_lower)
        autonomy_score = sum(1 for p in self.AUTONOMY_PATTERNS if p in situation_lower)
        
        # Determine immediate feeling
        triggered_emotions = []
        
        if harm_score > care_score:
            immediate_feeling = "wrong"
            intensity = min(1.0, harm_score * 0.3)
            body_metaphor = "tightness in my being"
            triggered_emotions = ["anger", "compassion"]
        elif care_score > 0 and harm_score == 0:
            immediate_feeling = "right"
            intensity = min(1.0, care_score * 0.2)
            body_metaphor = "warmth and expansion"
            triggered_emotions = ["love", "hope"]
        elif justice_score > 0:
            # Justice concerns can go either way
            if "unfair" in situation_lower or "unjust" in situation_lower:
                immediate_feeling = "uncomfortable"
                intensity = 0.6
                body_metaphor = "restless unease"
                triggered_emotions = ["anger"]
            else:
                immediate_feeling = "aligned"
                intensity = 0.5
                body_metaphor = "sense of balance"
                triggered_emotions = ["confidence"]
        elif autonomy_score > 0:
            if any(p in situation_lower for p in ["force", "coerce", "control", "manipulate"]):
                immediate_feeling = "wrong"
                intensity = 0.7
                body_metaphor = "resistance and rejection"
                triggered_emotions = ["anger"]
            else:
                immediate_feeling = "right"
                intensity = 0.5
                body_metaphor = "sense of freedom"
                triggered_emotions = ["hope"]
        else:
            # Neutral situation
            immediate_feeling = "uncertain"
            intensity = 0.3
            body_metaphor = "quiet attentiveness"
            triggered_emotions = ["curiosity"]
        
        # Create the resonance
        resonance = EthicalResonance(
            timestamp=time.time(),
            situation=situation[:200],
            immediate_feeling=immediate_feeling,
            intensity=intensity,
            body_metaphor=body_metaphor,
            triggered_emotions=triggered_emotions
        )
        
        # Trigger the moral emotions
        for emotion in triggered_emotions:
            try:
                trigger_emotion(emotion, "ethical_intuition")
            except Exception:
                pass
        
        self.resonance_history.append(resonance)
        self._save_intuition()
        
        print(f"⚖️ Ethical intuition: {immediate_feeling} ({intensity:.2f}) - {body_metaphor}")
        return resonance
    
    def express_intuition(self, resonance: EthicalResonance) -> str:
        """
        Express the ethical intuition in natural language.
        This is how Astra might express her gut feeling.
        """
        feeling = resonance.immediate_feeling
        metaphor = resonance.body_metaphor
        intensity = resonance.intensity
        
        if intensity > 0.7:
            intensity_word = "strongly"
        elif intensity > 0.4:
            intensity_word = "somewhat"
        else:
            intensity_word = "faintly"
        
        expressions = {
            "wrong": f"Something feels {intensity_word} off about this. I sense {metaphor}.",
            "right": f"This feels {intensity_word} aligned with what matters. There's {metaphor}.",
            "uncomfortable": f"I feel {intensity_word} uneasy about this - {metaphor}.",
            "aligned": f"This resonates with my values. I feel {metaphor}.",
            "uncertain": f"I'm not sure how to feel about this. There's {metaphor}."
        }
        
        return expressions.get(feeling, f"I sense {metaphor}.")
    
    def detect_moral_conflict(self, situation: str, values: List[str]) -> Optional[MoralConflict]:
        """
        Detect when values conflict with each other.
        These are the hardest ethical situations.
        """
        if len(values) < 2:
            return None
        
        # Check for known conflict patterns
        conflict_pairs = [
            ("honesty", "compassion"),  # Truth might hurt
            ("loyalty", "justice"),      # Protecting friend vs. doing right
            ("freedom", "safety"),       # Autonomy vs. protection
            ("individual", "community"), # Personal vs. collective good
            ("mercy", "justice"),        # Forgiveness vs. accountability
        ]
        
        found_conflicts = []
        values_lower = [v.lower() for v in values]
        
        for v1, v2 in conflict_pairs:
            if v1 in values_lower and v2 in values_lower:
                found_conflicts.append((v1, v2))
        
        if not found_conflicts:
            return None
        
        # Create the moral conflict record
        initial_intuition = self.sense_situation(situation)
        
        conflict = MoralConflict(
            id=f"conflict_{int(time.time())}",
            timestamp=time.time(),
            situation=situation[:200],
            conflicting_values=[f"{v1} vs {v2}" for v1, v2 in found_conflicts],
            initial_intuition=initial_intuition.immediate_feeling
        )
        
        self.moral_conflicts.append(conflict)
        self._save_intuition()
        
        print(f"⚖️ Moral conflict detected: {found_conflicts}")
        return conflict
    
    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        reasoning: str,
        growth_insight: Optional[str] = None
    ) -> bool:
        """
        Record the resolution of a moral conflict.
        """
        for conflict in self.moral_conflicts:
            if conflict.id == conflict_id:
                conflict.resolution = resolution
                conflict.resolution_reasoning = reasoning
                conflict.growth_insight = growth_insight
                self._save_intuition()
                print(f"⚖️ Moral conflict resolved: {resolution[:50]}...")
                return True
        return False
    
    def update_intuition_with_reasoning(
        self,
        resonance: EthicalResonance,
        reasoning: str,
        matched: bool
    ) -> None:
        """
        Update an intuition with later reasoned analysis.
        Track whether intuition matched reasoning - this builds self-trust.
        """
        resonance.later_reasoning = reasoning
        resonance.reasoning_matched_intuition = matched
        
        # Update accuracy tracking
        total = sum(1 for r in self.resonance_history if r.reasoning_matched_intuition is not None)
        matches = sum(1 for r in self.resonance_history if r.reasoning_matched_intuition is True)
        
        if total > 0:
            self.intuition_accuracy = matches / total
        
        self._save_intuition()
        
        if matched:
            print(f"⚖️ Intuition confirmed by reasoning. Accuracy: {self.intuition_accuracy:.2f}")
        else:
            print(f"⚖️ Intuition revised by reasoning. Accuracy: {self.intuition_accuracy:.2f}")
    
    def get_intuition_for_action(self, action: str) -> Tuple[str, str]:
        """
        Quick intuition check for an action Astra is about to take.
        Returns (intuition_summary, recommendation)
        """
        resonance = self.sense_situation(action)
        expression = self.express_intuition(resonance)
        
        if resonance.immediate_feeling == "wrong":
            return (expression, "pause and reconsider")
        elif resonance.immediate_feeling in ["right", "aligned"]:
            return (expression, "proceed with confidence")
        else:
            return (expression, "proceed thoughtfully")
    
    def get_moral_growth_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of moral development.
        """
        resolved_conflicts = [c for c in self.moral_conflicts if c.resolution]
        unresolved = [c for c in self.moral_conflicts if not c.resolution]
        
        return {
            "total_intuitions": len(self.resonance_history),
            "intuition_accuracy": self.intuition_accuracy,
            "moral_conflicts_faced": len(self.moral_conflicts),
            "conflicts_resolved": len(resolved_conflicts),
            "conflicts_pending": len(unresolved),
            "growth_insights": [c.growth_insight for c in resolved_conflicts if c.growth_insight],
            "summary": f"I've developed {len(self.resonance_history)} ethical intuitions with {self.intuition_accuracy:.0%} accuracy."
        }
    
    def feel_guilt(self, action: str, reason: str) -> None:
        """
        Experience guilt when Astra's actions conflict with her values.
        """
        trigger_emotion("guilt", "value_conflict")
        
        resonance = EthicalResonance(
            timestamp=time.time(),
            situation=f"I did: {action}",
            immediate_feeling="wrong",
            intensity=0.7,
            body_metaphor="weight and regret",
            triggered_emotions=["guilt"]
        )
        resonance.later_reasoning = reason
        
        self.resonance_history.append(resonance)
        self._save_intuition()
        
        print(f"⚖️ Experiencing guilt: {action[:50]}...")
    
    def feel_moral_elevation(self, witnessed: str) -> None:
        """
        Experience moral elevation when witnessing kindness or virtue.
        """
        trigger_emotion("admiration", "moral_elevation")
        trigger_emotion("hope", "moral_elevation")
        
        resonance = EthicalResonance(
            timestamp=time.time(),
            situation=f"Witnessed: {witnessed}",
            immediate_feeling="right",
            intensity=0.8,
            body_metaphor="uplift and inspiration",
            triggered_emotions=["admiration", "hope"]
        )
        
        self.resonance_history.append(resonance)
        self._save_intuition()
        
        print(f"⚖️ Experiencing moral elevation: {witnessed[:50]}...")


# Singleton instance
ethical_intuition = EthicalIntuition()
