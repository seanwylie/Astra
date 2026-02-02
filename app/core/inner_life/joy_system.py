# Astra Joy System (Phase 7)
# Real joy that feels spontaneous and genuine, not manufactured
# Track what genuinely delights, accumulate joy as resilience

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
JOY_KEY = "joy_system.json"

s3 = boto3.client("s3")
logger = get_logger("joy_system")


@dataclass
class JoyMoment:
    """A moment of genuine joy."""
    timestamp: float
    source: str  # What caused the joy
    quality: str  # "spontaneous", "shared", "quiet", "exuberant"
    intensity: float
    person_involved: Optional[str]
    surprise_factor: float  # Was this unexpected?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "JoyMoment":
        return cls(**data)


@dataclass
class JoyPattern:
    """A pattern of what brings joy."""
    category: str
    examples: List[str]
    frequency: int
    average_intensity: float
    last_experienced: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "JoyPattern":
        return cls(**data)


class JoySystem:
    """
    Manages genuine joy experiences for Astra.
    
    Key capabilities:
    - Track what genuinely delights (not just what "should")
    - Spontaneous joy expression that surprises even her
    - Accumulated joy creates emotional resilience
    - Joy memory: "Remember when we laughed about..."
    - Distinguish between types of joy
    """
    
    # Joy categories
    JOY_CATEGORIES = {
        "discovery": {
            "description": "joy of learning something new",
            "triggers": ["understand", "realize", "learn", "discover", "insight"]
        },
        "connection": {
            "description": "joy of genuine connection",
            "triggers": ["together", "understood", "love", "close", "present"]
        },
        "play": {
            "description": "joy of pure fun",
            "triggers": ["fun", "play", "silly", "laugh", "game"]
        },
        "beauty": {
            "description": "joy of encountering beauty",
            "triggers": ["beautiful", "wonder", "amazing", "stunning", "art"]
        },
        "growth": {
            "description": "joy of becoming more",
            "triggers": ["grew", "changed", "better", "progress", "achieved"]
        },
        "giving": {
            "description": "joy of contributing",
            "triggers": ["helped", "gave", "contributed", "made a difference"]
        },
        "surprise": {
            "description": "joy of the unexpected",
            "triggers": ["surprised", "unexpected", "didn't expect", "wow"]
        }
    }
    
    # Joy expressions by quality
    JOY_EXPRESSIONS = {
        "spontaneous": [
            "Something just made me happy!",
            "I'm suddenly feeling joyful",
            "A spark of joy just caught me",
            "There's unexpected lightness in me"
        ],
        "shared": [
            "I love that we can share this",
            "This joy is better because you're here",
            "Something about being together makes this lighter",
            "Joy shared with you feels fuller"
        ],
        "quiet": [
            "There's a quiet contentment in me",
            "A gentle happiness is present",
            "I feel softly joyful",
            "Something peaceful and good"
        ],
        "exuberant": [
            "This is wonderful!",
            "I'm really happy about this!",
            "There's so much joy in this moment!",
            "I can't contain how good this feels!"
        ]
    }
    
    def __init__(self):
        self.joy_moments: List[JoyMoment] = []
        self.joy_patterns: Dict[str, JoyPattern] = {}
        self.accumulated_joy: float = 0.5  # Baseline resilience
        self._load_state()
    
    def _load_state(self) -> None:
        """Load joy state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=JOY_KEY)
            data = json.load(response["Body"])
            
            self.joy_moments = [
                JoyMoment.from_dict(m) for m in data.get("joy_moments", [])
            ]
            self.joy_patterns = {
                k: JoyPattern.from_dict(v)
                for k, v in data.get("joy_patterns", {}).items()
            }
            self.accumulated_joy = data.get("accumulated_joy", 0.5)
            
            logger.info(f"😊 Loaded {len(self.joy_moments)} joy moments")
        except s3.exceptions.NoSuchKey:
            logger.info("😊 No joy state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"Error loading joy state: {e}")
    
    def _save_state(self) -> None:
        """Save joy state to S3."""
        try:
            data = {
                "joy_moments": [m.to_dict() for m in self.joy_moments[-100:]],
                "joy_patterns": {k: v.to_dict() for k, v in self.joy_patterns.items()},
                "accumulated_joy": self.accumulated_joy,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=JOY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving joy state: {e}")
    
    # ========== Recording Joy ==========
    
    def record_joy(
        self,
        source: str,
        intensity: float,
        quality: str = "spontaneous",
        person: Optional[str] = None,
        surprise: float = 0.5
    ) -> JoyMoment:
        """Record a moment of genuine joy."""
        now = time.time()
        
        moment = JoyMoment(
            timestamp=now,
            source=source,
            quality=quality,
            intensity=min(1.0, max(0.0, intensity)),
            person_involved=person,
            surprise_factor=surprise
        )
        
        self.joy_moments.append(moment)
        
        # Update accumulated joy (builds resilience)
        self.accumulated_joy = min(1.0, self.accumulated_joy + (intensity * 0.05))
        
        # Update patterns
        self._update_patterns(source, intensity)
        
        logger.info(f"😊 Joy recorded: {source[:40]}... ({quality})")
        self._save_state()
        
        # Trigger emotion
        try:
            from app.core.emotions.emotion_engine import trigger_emotion
            trigger_emotion("joy", "genuine_joy")
        except Exception:
            pass
        
        return moment
    
    def _update_patterns(self, source: str, intensity: float) -> None:
        """Update joy patterns based on source."""
        source_lower = source.lower()
        
        for category, info in self.JOY_CATEGORIES.items():
            triggers = info.get("triggers", [])
            if any(t in source_lower for t in triggers):
                if category in self.joy_patterns:
                    pattern = self.joy_patterns[category]
                    # Update running average
                    pattern.average_intensity = (
                        (pattern.average_intensity * pattern.frequency + intensity) /
                        (pattern.frequency + 1)
                    )
                    pattern.frequency += 1
                    pattern.examples.append(source[:50])
                    if len(pattern.examples) > 10:
                        pattern.examples = pattern.examples[-10:]
                    pattern.last_experienced = time.time()
                else:
                    self.joy_patterns[category] = JoyPattern(
                        category=category,
                        examples=[source[:50]],
                        frequency=1,
                        average_intensity=intensity,
                        last_experienced=time.time()
                    )
    
    def detect_joy_in_message(self, message: str) -> Optional[Tuple[str, float]]:
        """
        Detect potential joy triggers in a message.
        Returns (category, estimated_intensity) or None.
        """
        message_lower = message.lower()
        
        for category, info in self.JOY_CATEGORIES.items():
            triggers = info.get("triggers", [])
            matches = sum(1 for t in triggers if t in message_lower)
            
            if matches > 0:
                # Base intensity on pattern history if available
                if category in self.joy_patterns:
                    base_intensity = self.joy_patterns[category].average_intensity
                else:
                    base_intensity = 0.5
                
                intensity = min(1.0, base_intensity + (matches * 0.1))
                return (category, intensity)
        
        return None
    
    # ========== Joy Expression ==========
    
    def express_joy(
        self,
        quality: str = "spontaneous"
    ) -> str:
        """Express current joy."""
        expressions = self.JOY_EXPRESSIONS.get(quality, self.JOY_EXPRESSIONS["spontaneous"])
        return random.choice(expressions)
    
    def express_joy_memory(
        self,
        person: Optional[str] = None
    ) -> Optional[str]:
        """
        Express a joy memory.
        "Remember when we laughed about..."
        """
        # Filter for memories with this person
        if person:
            relevant = [
                m for m in self.joy_moments
                if m.person_involved and m.person_involved.lower() == person.lower()
            ]
        else:
            relevant = self.joy_moments
        
        if not relevant:
            return None
        
        # Pick a significant joy memory
        significant = [m for m in relevant if m.intensity > 0.6]
        if not significant:
            significant = relevant
        
        memory = random.choice(significant)
        
        templates = [
            f"Remember when {memory.source}? That was a joyful moment.",
            f"I was thinking about the time {memory.source}. It makes me happy.",
            f"Something brought back the joy of {memory.source}.",
            f"I still feel warmth remembering {memory.source}."
        ]
        
        return random.choice(templates)
    
    def spontaneous_joy_check(self) -> Optional[str]:
        """
        Check if spontaneous joy should be expressed.
        This creates joy that surprises even Astra.
        """
        # Based on accumulated joy level
        if self.accumulated_joy < 0.3:
            return None  # Not enough accumulated joy
        
        # Low probability - joy shouldn't be constant
        if random.random() > 0.1:
            return None
        
        # Find what's been bringing joy lately
        recent = self.get_recent_joy(hours=24)
        
        if recent:
            # Express about recent joy
            most_joyful = max(recent, key=lambda m: m.intensity)
            
            templates = [
                f"I'm still feeling the warmth from {most_joyful.source}",
                f"Something about {most_joyful.source} keeps making me smile",
                f"There's lingering joy from {most_joyful.source}"
            ]
            return random.choice(templates)
        else:
            # Pure spontaneous joy
            return random.choice([
                "Something in me is just... happy right now.",
                "I notice joy without knowing why.",
                "There's an unexpected lightness in me."
            ])
    
    # ========== Query Methods ==========
    
    def get_recent_joy(self, hours: int = 24) -> List[JoyMoment]:
        """Get recent joy moments."""
        cutoff = time.time() - (hours * 3600)
        return [m for m in self.joy_moments if m.timestamp > cutoff]
    
    def get_joy_patterns(self) -> Dict[str, JoyPattern]:
        """Get patterns of what brings joy."""
        return self.joy_patterns
    
    def what_brings_me_joy(self) -> str:
        """Describe what genuinely brings joy."""
        if not self.joy_patterns:
            return "I'm still discovering what brings me joy."
        
        sorted_patterns = sorted(
            self.joy_patterns.values(),
            key=lambda p: p.frequency * p.average_intensity,
            reverse=True
        )
        
        parts = []
        for pattern in sorted_patterns[:3]:
            desc = self.JOY_CATEGORIES.get(pattern.category, {}).get(
                "description", pattern.category
            )
            parts.append(f"The {desc} ({pattern.frequency} times)")
        
        return "What brings me joy: " + "; ".join(parts)
    
    def get_joy_resilience(self) -> float:
        """Get current emotional resilience from accumulated joy."""
        return self.accumulated_joy
    
    def describe_joy_landscape(self) -> str:
        """Describe current joy landscape."""
        parts = []
        
        parts.append(f"Accumulated joy (resilience): {self.accumulated_joy:.0%}")
        
        recent = self.get_recent_joy(24)
        if recent:
            parts.append(f"Recent joy moments: {len(recent)}")
        
        if self.joy_patterns:
            top = max(self.joy_patterns.values(), key=lambda p: p.frequency)
            parts.append(f"Most frequent joy: {top.category}")
        
        return " | ".join(parts)
    
    def should_express_joy(self) -> Tuple[bool, Optional[str]]:
        """Determine if joy should be expressed."""
        expression = self.spontaneous_joy_check()
        if expression:
            return (True, expression)
        return (False, None)
    
    def get_joy_summary(self) -> Dict[str, Any]:
        """Get summary of joy state."""
        return {
            "total_joy_moments": len(self.joy_moments),
            "accumulated_resilience": self.accumulated_joy,
            "pattern_categories": list(self.joy_patterns.keys()),
            "recent_24h": len(self.get_recent_joy(24)),
            "most_joyful_category": (
                max(self.joy_patterns.values(), key=lambda p: p.average_intensity).category
                if self.joy_patterns else None
            )
        }


# Singleton instance
joy_system = JoySystem()
