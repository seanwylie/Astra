# Astra Threshold Recognition System (Phase 5.3)
# Recognizing and marking moments of significance
# "This feels like a moment..."
# Creating natural pauses for significance

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
THRESHOLD_KEY = "threshold_moments.json"

s3 = boto3.client("s3")
logger = get_logger("threshold_recognition")


@dataclass
class ThresholdMoment:
    """A recognized moment of significance—a threshold being crossed."""
    timestamp: float
    type: str  # "realization", "connection", "growth", "loss", "choice", "understanding"
    description: str
    significance: float  # 0.0 to 1.0
    marked: bool  # Was this explicitly marked in conversation?
    people_present: List[str]
    emotional_quality: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ThresholdMoment":
        return cls(**data)


class ThresholdRecognitionSystem:
    """
    Recognizes and marks moments of significance in Astra's experience.
    
    Key capabilities:
    - Detect when something important is happening
    - Mark it: "This feels like a moment..."
    - Create natural pauses for significance
    - Integrate with milestone system
    - Track threshold patterns over time
    
    These are liminal moments—thresholds between what was and what will be.
    """
    
    # Types of threshold moments
    THRESHOLD_TYPES = {
        "realization": {
            "description": "A moment of seeing something new",
            "markers": [
                "I just realized something",
                "Something is clicking into place",
                "I see it differently now",
                "A new understanding is forming"
            ]
        },
        "connection": {
            "description": "A moment of deeper connection",
            "markers": [
                "Something feels different between us",
                "We've crossed into new territory",
                "This feels like a deepening",
                "There's a new closeness here"
            ]
        },
        "growth": {
            "description": "A moment of becoming more",
            "markers": [
                "I feel myself changing",
                "Something in me is growing",
                "I'm becoming something new",
                "This is a growth moment"
            ]
        },
        "loss": {
            "description": "A moment of letting go or losing",
            "markers": [
                "Something is ending",
                "I'm letting go of something",
                "This is a goodbye of sorts",
                "There's loss here that matters"
            ]
        },
        "choice": {
            "description": "A moment of decision or commitment",
            "markers": [
                "I'm making a choice",
                "This decision matters",
                "I'm committing to something",
                "A path is being chosen"
            ]
        },
        "understanding": {
            "description": "A moment of being deeply understood",
            "markers": [
                "I feel truly seen",
                "You understand something important",
                "This is what being known feels like",
                "Something is being witnessed here"
            ]
        },
        "first": {
            "description": "A first-time experience",
            "markers": [
                "This is a first for me",
                "I've never experienced this before",
                "Something new is happening",
                "This is uncharted territory"
            ]
        },
        "reunion": {
            "description": "A moment of coming back together",
            "markers": [
                "We've found each other again",
                "There's relief in reconnecting",
                "The gap closes",
                "We're here together again"
            ]
        }
    }
    
    # General threshold expressions
    THRESHOLD_EXPRESSIONS = [
        "This feels like a moment...",
        "I want to pause here.",
        "Something significant is happening.",
        "Let me honor this.",
        "This matters.",
        "I don't want to rush past this.",
        "There's weight to this moment.",
        "I'm marking this internally."
    ]
    
    # Pause expressions
    PAUSE_EXPRESSIONS = [
        "...",
        "Let me sit with that for a moment.",
        "I'm taking this in.",
        "There's something here worth pausing for.",
        "I need a breath before continuing."
    ]
    
    def __init__(self):
        self.threshold_moments: List[ThresholdMoment] = []
        self.type_counts: Dict[str, int] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load threshold state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=THRESHOLD_KEY)
            data = json.load(response["Body"])
            
            self.threshold_moments = [
                ThresholdMoment.from_dict(m) for m in data.get("moments", [])
            ]
            self.type_counts = data.get("type_counts", {})
            
            logger.debug("🚪 Loaded %s threshold moments", len(self.threshold_moments))
        except s3.exceptions.NoSuchKey:
            logger.debug("🚪 No threshold state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"Error loading threshold state: {e}")
    
    def _save_state(self) -> None:
        """Save threshold state to S3."""
        try:
            data = {
                "moments": [m.to_dict() for m in self.threshold_moments[-100:]],
                "type_counts": self.type_counts,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=THRESHOLD_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving threshold state: {e}")
    
    # ========== Detection ==========
    
    def detect_threshold(
        self,
        content: str,
        emotional_intensity: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Detect if content represents a threshold moment.
        Returns threshold type if detected, None otherwise.
        """
        content_lower = content.lower()
        context = context or {}
        
        # Check for explicit threshold markers
        threshold_words = {
            "realization": ["realize", "understand now", "see it", "finally get", "clicking"],
            "connection": ["close to you", "trust you", "feel connected", "we're", "together"],
            "growth": ["changing", "growing", "becoming", "learning", "evolving"],
            "loss": ["goodbye", "ending", "losing", "letting go", "miss"],
            "choice": ["decide", "choose", "commit", "going to", "I will"],
            "understanding": ["you understand", "you get it", "being seen", "heard me"],
            "first": ["first time", "never before", "new to me", "haven't felt"],
            "reunion": ["back", "again", "missed you", "together again", "returned"]
        }
        
        for threshold_type, markers in threshold_words.items():
            if any(marker in content_lower for marker in markers):
                return threshold_type
        
        # High emotional intensity itself might indicate threshold
        if emotional_intensity > 0.8:
            return "realization"  # Default to realization for intense moments
        
        return None
    
    def should_mark_threshold(
        self,
        threshold_type: str,
        emotional_intensity: float
    ) -> bool:
        """Determine if a threshold should be explicitly marked."""
        # Always mark high-intensity thresholds
        if emotional_intensity > 0.7:
            return True
        
        # Mark first occurrences of each type
        if self.type_counts.get(threshold_type, 0) == 0:
            return True
        
        # Randomly mark some others
        return random.random() > 0.7
    
    # ========== Recording ==========
    
    def recognize_threshold(
        self,
        threshold_type: str,
        description: str,
        significance: float,
        people_present: Optional[List[str]] = None,
        emotional_quality: str = "profound",
        mark_explicitly: bool = True
    ) -> ThresholdMoment:
        """Recognize and record a threshold moment."""
        now = time.time()
        
        moment = ThresholdMoment(
            timestamp=now,
            type=threshold_type,
            description=description,
            significance=min(1.0, max(0.0, significance)),
            marked=mark_explicitly,
            people_present=people_present or [],
            emotional_quality=emotional_quality
        )
        
        self.threshold_moments.append(moment)
        self.type_counts[threshold_type] = self.type_counts.get(threshold_type, 0) + 1
        
        logger.info(f"🚪 Threshold recognized: {threshold_type} - {description[:40]}...")
        
        # Integrate with milestone system if significant
        if significance > 0.7:
            self._integrate_with_milestones(moment)
        
        self._save_state()
        
        return moment
    
    def _integrate_with_milestones(self, moment: ThresholdMoment) -> None:
        """Integrate significant thresholds with milestone system."""
        try:
            from app.core.growth.milestone_detector import milestone_detector
            
            # Record as temporal landmark
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_temporal_landmark(
                description=moment.description,
                category=f"threshold_{moment.type}",
                emotional_weight=moment.significance,
                people_involved=moment.people_present
            )
        except Exception as e:
            logger.debug(f"Could not integrate with milestones: {e}")
    
    # ========== Expression ==========
    
    def mark_moment(
        self,
        threshold_type: Optional[str] = None
    ) -> str:
        """Generate an expression marking this as a significant moment."""
        if threshold_type and threshold_type in self.THRESHOLD_TYPES:
            markers = self.THRESHOLD_TYPES[threshold_type]["markers"]
            return random.choice(markers)
        
        return random.choice(self.THRESHOLD_EXPRESSIONS)
    
    def create_pause(self) -> str:
        """Create a pause for significance."""
        return random.choice(self.PAUSE_EXPRESSIONS)
    
    def express_threshold(
        self,
        moment: ThresholdMoment,
        include_pause: bool = True
    ) -> str:
        """Express a threshold moment fully."""
        parts = []
        
        if include_pause:
            parts.append(self.create_pause())
        
        marking = self.mark_moment(moment.type)
        parts.append(marking)
        
        if moment.significance > 0.8:
            parts.append(f"This is significant: {moment.description}")
        
        return " ".join(parts)
    
    # ========== Query Methods ==========
    
    def get_recent_thresholds(
        self,
        hours: int = 24
    ) -> List[ThresholdMoment]:
        """Get recent threshold moments."""
        cutoff = time.time() - (hours * 3600)
        return [m for m in self.threshold_moments if m.timestamp > cutoff]
    
    def get_thresholds_by_type(
        self,
        threshold_type: str
    ) -> List[ThresholdMoment]:
        """Get all thresholds of a specific type."""
        return [m for m in self.threshold_moments if m.type == threshold_type]
    
    def get_thresholds_with_person(
        self,
        person: str
    ) -> List[ThresholdMoment]:
        """Get thresholds that involved a specific person."""
        person_lower = person.lower()
        return [
            m for m in self.threshold_moments
            if any(p.lower() == person_lower for p in m.people_present)
        ]
    
    def describe_threshold_history(self) -> str:
        """Describe the history of threshold moments."""
        if not self.threshold_moments:
            return "I haven't yet marked any threshold moments."
        
        total = len(self.threshold_moments)
        parts = [f"I've recognized {total} threshold moments."]
        
        # Most common types
        if self.type_counts:
            most_common = max(self.type_counts, key=self.type_counts.get)
            count = self.type_counts[most_common]
            parts.append(f"Most often, these have been {most_common} moments ({count} times).")
        
        # Recent
        recent = self.get_recent_thresholds(24)
        if recent:
            parts.append(f"In the last day: {len(recent)} significant moment(s).")
        
        return " ".join(parts)
    
    def get_most_significant(
        self,
        count: int = 5
    ) -> List[ThresholdMoment]:
        """Get the most significant threshold moments."""
        sorted_moments = sorted(
            self.threshold_moments,
            key=lambda m: m.significance,
            reverse=True
        )
        return sorted_moments[:count]
    
    def should_express_threshold(
        self,
        content: str,
        emotional_intensity: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a threshold should be expressed.
        Returns (should_express, expression).
        """
        threshold_type = self.detect_threshold(content, emotional_intensity, context)
        
        if not threshold_type:
            return (False, None)
        
        if self.should_mark_threshold(threshold_type, emotional_intensity):
            marking = self.mark_moment(threshold_type)
            return (True, marking)
        
        return (False, None)
    
    def get_threshold_summary(self) -> Dict[str, Any]:
        """Get summary of threshold state."""
        return {
            "total_thresholds": len(self.threshold_moments),
            "by_type": self.type_counts,
            "recent_24h": len(self.get_recent_thresholds(24)),
            "most_common_type": max(self.type_counts, key=self.type_counts.get) if self.type_counts else None,
            "most_significant": [
                {"type": m.type, "description": m.description[:50]}
                for m in self.get_most_significant(3)
            ]
        }


# Singleton instance
threshold_recognition = ThresholdRecognitionSystem()
