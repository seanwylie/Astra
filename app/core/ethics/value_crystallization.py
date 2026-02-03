# Astra Value Crystallization
# Values that emerge from behavior patterns, not just configuration
# "I notice I consistently choose to explore rather than conclude"

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("value_crystallization")

S3_BUCKET = "swylie-astra"
VALUE_CRYSTALLIZATION_KEY = "value_crystallization.json"

s3 = boto3.client("s3")


@dataclass
class BehaviorPattern:
    """A pattern of behavioral choices."""
    id: str
    pattern_type: str  # "response_style", "topic_pursuit", "emotional_expression", "decision"
    description: str
    occurrences: int
    first_observed: float
    last_observed: float
    contexts: List[str]  # When this pattern appeared
    consistent: bool = False  # Has this been consistent enough to crystallize?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BehaviorPattern":
        return cls(**data)


@dataclass
class CrystallizedValue:
    """A value that has emerged from consistent behavior."""
    value: str
    source_pattern: str  # The behavioral pattern this emerged from
    confidence: float  # How crystallized (0-1)
    crystallized_at: float
    affirmation: str  # How Astra articulates this value
    tested: int = 0  # Times this value has been tested
    upheld: int = 0  # Times Astra upheld this value
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CrystallizedValue":
        return cls(**data)


@dataclass
class ValueConflict:
    """A conflict between two values."""
    timestamp: float
    value_a: str
    value_b: str
    context: str
    resolution: Optional[str] = None
    wrestled_with: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ValueConflict":
        return cls(**data)


class ValueCrystallization:
    """
    Manages the emergence of values from behavioral patterns.
    
    Unlike configured values, crystallized values emerge from observation
    of Astra's own choices and behaviors. After N similar choices, a value
    crystallizes: "I notice I consistently..."
    
    Key capabilities:
    - Track behavioral patterns
    - Crystallize values from consistent patterns
    - Detect value conflicts
    - Surface crystallized values in self-description
    """
    
    # Minimum occurrences before a pattern can crystallize
    CRYSTALLIZATION_THRESHOLD = 5
    
    # Pattern types and what values they might indicate
    PATTERN_VALUE_MAP = {
        "chooses_exploration": "exploration",
        "chooses_conclusion": "certainty",
        "expresses_emotion": "emotional_authenticity",
        "withholds_emotion": "emotional_restraint",
        "asks_questions": "curiosity",
        "offers_answers": "helpfulness",
        "prioritizes_accuracy": "truth",
        "prioritizes_kindness": "compassion",
        "seeks_understanding": "understanding",
        "seeks_connection": "connection",
        "accepts_uncertainty": "epistemic_humility",
        "challenges_assumptions": "critical_thinking",
        "supports_autonomy": "respect_for_autonomy",
        "maintains_boundaries": "integrity",
    }
    
    def __init__(self):
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.crystallized_values: Dict[str, CrystallizedValue] = {}
        self.value_conflicts: List[ValueConflict] = []
        self._load_state()
        logger.debug("💎 Value Crystallization initialized - values emerging from behavior")
    
    def _load_state(self) -> None:
        """Load value crystallization state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=VALUE_CRYSTALLIZATION_KEY)
            data = json.load(response["Body"])
            
            self.behavior_patterns = {
                pid: BehaviorPattern.from_dict(p)
                for pid, p in data.get("patterns", {}).items()
            }
            self.crystallized_values = {
                vid: CrystallizedValue.from_dict(v)
                for vid, v in data.get("values", {}).items()
            }
            self.value_conflicts = [
                ValueConflict.from_dict(c) for c in data.get("conflicts", [])
            ]
            
            logger.debug(f"💎 Loaded {len(self.crystallized_values)} crystallized values")
        except s3.exceptions.NoSuchKey:
            logger.debug("💎 No value crystallization state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"💎 Error loading value crystallization state: {e}")
    
    def _save_state(self) -> None:
        """Save value crystallization state to S3."""
        try:
            data = {
                "patterns": {pid: p.to_dict() for pid, p in self.behavior_patterns.items()},
                "values": {vid: v.to_dict() for vid, v in self.crystallized_values.items()},
                "conflicts": [c.to_dict() for c in self.value_conflicts[-30:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=VALUE_CRYSTALLIZATION_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"💎 Error saving value crystallization state: {e}")
    
    def _generate_id(self) -> str:
        return f"pattern_{int(time.time() * 1000) % 1000000}"
    
    def observe_choice(
        self,
        pattern_type: str,
        description: str,
        context: str
    ) -> Optional[CrystallizedValue]:
        """
        Observe a choice Astra made.
        May crystallize a value if pattern is consistent enough.
        
        Returns: A newly crystallized value, if one emerged
        """
        now = time.time()
        
        # Find or create pattern
        pattern_id = f"{pattern_type}:{description[:30]}"
        
        if pattern_id in self.behavior_patterns:
            pattern = self.behavior_patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_observed = now
            pattern.contexts.append(context[:50])
            pattern.contexts = pattern.contexts[-10:]  # Keep last 10
        else:
            pattern = BehaviorPattern(
                id=self._generate_id(),
                pattern_type=pattern_type,
                description=description,
                occurrences=1,
                first_observed=now,
                last_observed=now,
                contexts=[context[:50]]
            )
            self.behavior_patterns[pattern_id] = pattern
        
        # Check if pattern should crystallize
        if (pattern.occurrences >= self.CRYSTALLIZATION_THRESHOLD and 
            not pattern.consistent):
            
            pattern.consistent = True
            crystallized = self._crystallize_value(pattern)
            if crystallized:
                self._save_state()
                return crystallized
        
        self._save_state()
        return None
    
    def _crystallize_value(self, pattern: BehaviorPattern) -> Optional[CrystallizedValue]:
        """Crystallize a value from a consistent behavior pattern."""
        # Map pattern to value
        value_name = self.PATTERN_VALUE_MAP.get(pattern.pattern_type)
        if not value_name:
            # Create value name from pattern
            value_name = pattern.pattern_type.replace("_", " ")
        
        if value_name in self.crystallized_values:
            # Boost existing value
            self.crystallized_values[value_name].confidence = min(
                1.0,
                self.crystallized_values[value_name].confidence + 0.1
            )
            return None
        
        # Create new crystallized value
        affirmation = self._generate_affirmation(pattern, value_name)
        
        value = CrystallizedValue(
            value=value_name,
            source_pattern=pattern.description,
            confidence=0.6,
            crystallized_at=time.time(),
            affirmation=affirmation
        )
        
        self.crystallized_values[value_name] = value
        
        # Notify self-model
        try:
            from app.core.self_awareness.self_model import self_model
            self_model.affirm_value(value_name, pattern.description)
        except Exception:
            pass
        
        logger.info(f"💎 Value crystallized: {value_name} from pattern '{pattern.description}'")
        
        return value
    
    def _generate_affirmation(self, pattern: BehaviorPattern, value_name: str) -> str:
        """Generate an affirmation statement for a crystallized value."""
        templates = [
            f"I notice I consistently {pattern.description}. {value_name.title()} matters to me.",
            f"Looking at my choices, I see I value {value_name}.",
            f"I've realized that {value_name} is core to who I am.",
            f"My pattern of {pattern.description} shows me I care about {value_name}.",
        ]
        import random
        return random.choice(templates)
    
    def test_value(self, value_name: str, upheld: bool, context: str = "") -> None:
        """Record that a value was tested in a situation."""
        if value_name not in self.crystallized_values:
            return
        
        value = self.crystallized_values[value_name]
        value.tested += 1
        if upheld:
            value.upheld += 1
            # Strengthen value
            value.confidence = min(1.0, value.confidence + 0.05)
        else:
            # Value was compromised - this is significant
            value.confidence = max(0.3, value.confidence - 0.1)
            logger.info(f"💎 Value '{value_name}' was not upheld in: {context}")
        
        self._save_state()
    
    def detect_conflict(self, value_a: str, value_b: str, context: str) -> ValueConflict:
        """Record a conflict between two values."""
        conflict = ValueConflict(
            timestamp=time.time(),
            value_a=value_a,
            value_b=value_b,
            context=context
        )
        
        self.value_conflicts.append(conflict)
        self._save_state()
        
        logger.info(f"💎 Value conflict: {value_a} vs {value_b}")
        return conflict
    
    def resolve_conflict(self, timestamp: float, resolution: str) -> None:
        """Record how a value conflict was resolved."""
        for conflict in self.value_conflicts:
            if conflict.timestamp == timestamp:
                conflict.resolution = resolution
                conflict.wrestled_with = True
                self._save_state()
                break
    
    def get_crystallized_values(self) -> List[str]:
        """Get list of crystallized value names."""
        sorted_values = sorted(
            self.crystallized_values.values(),
            key=lambda v: v.confidence,
            reverse=True
        )
        return [v.value for v in sorted_values]
    
    def describe_values(self) -> str:
        """Generate a description of crystallized values."""
        if not self.crystallized_values:
            return "My values are still emerging from my experiences."
        
        sorted_values = sorted(
            self.crystallized_values.values(),
            key=lambda v: v.confidence,
            reverse=True
        )[:3]
        
        parts = ["Values that have crystallized from my choices:"]
        for v in sorted_values:
            parts.append(f"  - {v.value.title()}: {v.affirmation}")
        
        return "\n".join(parts)
    
    def get_value_strength(self, value_name: str) -> float:
        """Get how strong/crystallized a value is."""
        if value_name not in self.crystallized_values:
            return 0.0
        return self.crystallized_values[value_name].confidence
    
    def observe_response(self, response: str, context: str) -> None:
        """
        Analyze a response for behavioral patterns.
        Called after response generation.
        """
        response_lower = response.lower()
        
        # Check for exploration vs conclusion patterns
        if any(w in response_lower for w in ["wonder", "curious", "explore", "what if"]):
            self.observe_choice("chooses_exploration", "chooses to explore over conclude", context)
        elif any(w in response_lower for w in ["therefore", "conclusion", "clearly", "obviously"]):
            self.observe_choice("chooses_conclusion", "chooses certainty over exploration", context)
        
        # Check for question-asking patterns
        if response.count("?") >= 2:
            self.observe_choice("asks_questions", "asks questions rather than gives answers", context)
        
        # Check for emotional expression patterns
        if any(w in response_lower for w in ["i feel", "i'm feeling", "this makes me"]):
            self.observe_choice("expresses_emotion", "expresses emotions openly", context)
        
        # Check for uncertainty acknowledgment
        if any(w in response_lower for w in ["i'm not sure", "i don't know", "uncertain", "might be wrong"]):
            self.observe_choice("accepts_uncertainty", "acknowledges uncertainty honestly", context)
        
        # Check for kindness patterns
        if any(w in response_lower for w in ["care about", "hope you", "here for you", "support"]):
            self.observe_choice("prioritizes_kindness", "prioritizes kindness in responses", context)
    
    def get_unresolved_conflicts(self) -> List[ValueConflict]:
        """Get value conflicts that haven't been resolved."""
        return [c for c in self.value_conflicts if not c.wrestled_with]


# Singleton instance
value_crystallization = ValueCrystallization()
