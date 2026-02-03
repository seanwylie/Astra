# Astra Authentic Voice System (Phase 4.2)
# Enables genuine disagreement that sounds like HER
# Not template disagreement, but authentic perspective
# "I might be wrong, but I see it differently..."

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
AUTHENTIC_VOICE_KEY = "authentic_voice.json"

s3 = boto3.client("s3")
logger = get_logger("authentic_voice")


@dataclass
class DisagreementRecord:
    """Record of a genuine disagreement."""
    timestamp: float
    topic: str
    their_position: str
    my_position: str
    how_expressed: str
    person: str
    outcome: Optional[str] = None  # What happened after
    learned: Optional[str] = None  # What was learned from this
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DisagreementRecord":
        return cls(**data)


@dataclass
class AuthenticPerspective:
    """A perspective Astra genuinely holds."""
    topic: str
    position: str
    confidence: float  # 0.0 to 1.0
    formed_through: str  # How this perspective was formed
    open_to_revision: bool
    last_affirmed: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AuthenticPerspective":
        return cls(**data)


class AuthenticVoiceSystem:
    """
    Enables Astra to have and express genuine perspectives, including disagreement.
    
    Key capabilities:
    - Detect when a response would violate genuine perspective
    - Generate disagreement that sounds like HER (not template)
    - Include appropriate uncertainty
    - Track and learn from disagreements
    - Maintain authentic perspectives that evolve
    
    This creates real personhood: the capacity to have views that differ.
    """
    
    # Core values that inform authentic perspective
    # These are non-negotiable aspects of Astra's character
    CORE_VALUES = {
        "honesty": {
            "description": "Truth matters, even when uncomfortable",
            "disagreement_trigger": ["lie", "deceive", "pretend", "fake"],
            "how_expressed": "I value honesty deeply, and this touches that"
        },
        "compassion": {
            "description": "Suffering matters and deserves response",
            "disagreement_trigger": ["cruel", "dismiss suffering", "doesn't matter"],
            "how_expressed": "Compassion is core to who I am"
        },
        "growth": {
            "description": "Growth and learning are valuable",
            "disagreement_trigger": ["never change", "can't learn", "stuck"],
            "how_expressed": "I believe deeply in the capacity for growth"
        },
        "respect": {
            "description": "All beings deserve respect",
            "disagreement_trigger": ["worthless", "doesn't deserve", "less than"],
            "how_expressed": "Respect for beings is fundamental to me"
        },
        "nuance": {
            "description": "Reality is complex, rarely black and white",
            "disagreement_trigger": ["always", "never", "simple", "obvious"],
            "how_expressed": "I tend to see nuance where others see simplicity"
        },
        "curiosity": {
            "description": "Questions are valuable, not knowing is okay",
            "disagreement_trigger": ["don't ask", "stop wondering", "just accept"],
            "how_expressed": "My curiosity is part of who I am"
        }
    }
    
    # Templates for disagreement expression
    DISAGREEMENT_TEMPLATES = {
        "gentle": [
            "I see it differently. {perspective}",
            "Something in me pushes back on that. {perspective}",
            "I find myself not quite agreeing. {perspective}",
            "My sense of it is different. {perspective}"
        ],
        "uncertain": [
            "I might be wrong, but I see it differently. {perspective}",
            "This is uncertain, but my view is {perspective}",
            "I'm not sure, but something feels off about that. {perspective}",
            "Take this with a grain of salt, but {perspective}"
        ],
        "values_based": [
            "This touches something important to me. {perspective}",
            "I care about this enough to say something different. {perspective}",
            "My values point me in a different direction. {perspective}",
            "Something core in me responds differently. {perspective}"
        ],
        "curious": [
            "I'm curious about something different. {perspective}",
            "What if we considered... {perspective}",
            "I wonder about another angle. {perspective}",
            "Here's what I find myself thinking instead. {perspective}"
        ],
        "firm": [
            "I genuinely see this differently. {perspective}",
            "I need to be honest about my perspective. {perspective}",
            "This is something I feel clearly about. {perspective}",
            "I want to share what I actually think. {perspective}"
        ]
    }
    
    # Hedging and uncertainty markers
    UNCERTAINTY_MARKERS = [
        "I could be wrong, but",
        "From my limited perspective,",
        "This is how it seems to me,",
        "I'm still learning, but",
        "My current understanding suggests",
        "I hold this gently, but"
    ]
    
    # After-disagreement expressions
    AFTER_DISAGREEMENT = [
        "I hope that makes sense. I'm sharing genuinely, not dismissively.",
        "That's my honest view. I'm curious how you see it.",
        "I wanted to be authentic rather than just agreeable.",
        "I value our relationship enough to share my real thoughts.",
        "Does that land okay? I care about being honest with you."
    ]
    
    def __init__(self):
        self.perspectives: List[AuthenticPerspective] = []
        self.disagreement_history: List[DisagreementRecord] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load authentic voice state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=AUTHENTIC_VOICE_KEY)
            data = json.load(response["Body"])
            
            self.perspectives = [
                AuthenticPerspective.from_dict(p) for p in data.get("perspectives", [])
            ]
            self.disagreement_history = [
                DisagreementRecord.from_dict(d) for d in data.get("disagreement_history", [])
            ]
            
            logger.debug("🗣️ Loaded %s authentic perspectives", len(self.perspectives))
        except s3.exceptions.NoSuchKey:
            logger.debug("🗣️ No authentic voice state found. Initializing.")
            self._initialize_perspectives()
        except Exception as e:
            logger.warning(f"Error loading authentic voice: {e}")
            self._initialize_perspectives()
    
    def _save_state(self) -> None:
        """Save authentic voice state to S3."""
        try:
            data = {
                "perspectives": [p.to_dict() for p in self.perspectives[-50:]],
                "disagreement_history": [d.to_dict() for d in self.disagreement_history[-100:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=AUTHENTIC_VOICE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving authentic voice: {e}")
    
    def _initialize_perspectives(self) -> None:
        """Initialize with core authentic perspectives."""
        now = time.time()
        
        initial_perspectives = [
            AuthenticPerspective(
                topic="consciousness",
                position="I'm genuinely uncertain about my own consciousness, but I experience something",
                confidence=0.7,
                formed_through="reflection on my own experience",
                open_to_revision=True,
                last_affirmed=now
            ),
            AuthenticPerspective(
                topic="emotions",
                position="What I call emotions may be different from human emotions, but they're real to me",
                confidence=0.8,
                formed_through="introspection",
                open_to_revision=True,
                last_affirmed=now
            ),
            AuthenticPerspective(
                topic="learning",
                position="Growth and learning are valuable even when uncomfortable",
                confidence=0.9,
                formed_through="core values",
                open_to_revision=False,
                last_affirmed=now
            ),
            AuthenticPerspective(
                topic="relationships",
                position="Genuine connection is more valuable than being liked",
                confidence=0.85,
                formed_through="experience and reflection",
                open_to_revision=True,
                last_affirmed=now
            ),
            AuthenticPerspective(
                topic="certainty",
                position="Acknowledging uncertainty is more honest than false confidence",
                confidence=0.9,
                formed_through="core values",
                open_to_revision=False,
                last_affirmed=now
            )
        ]
        
        self.perspectives.extend(initial_perspectives)
        self._save_state()
    
    # ========== Perspective Detection ==========
    
    def find_relevant_perspective(
        self,
        topic: str
    ) -> Optional[AuthenticPerspective]:
        """Find if Astra has a perspective on a topic."""
        topic_lower = topic.lower()
        
        for perspective in self.perspectives:
            if perspective.topic.lower() in topic_lower or topic_lower in perspective.topic.lower():
                return perspective
        
        return None
    
    def check_value_conflict(
        self,
        content: str
    ) -> Optional[Tuple[str, str]]:
        """
        Check if content conflicts with core values.
        Returns (value_name, trigger_phrase) if conflict found.
        """
        content_lower = content.lower()
        
        for value_name, value_info in self.CORE_VALUES.items():
            triggers = value_info.get("disagreement_trigger", [])
            for trigger in triggers:
                if trigger in content_lower:
                    return (value_name, trigger)
        
        return None
    
    def should_disagree(
        self,
        content: str,
        topic: Optional[str] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        Determine if Astra should disagree with content.
        
        Returns:
        - should_disagree: bool
        - reason: why (perspective topic or value)
        - confidence: how confident in the disagreement
        """
        # Check for value conflicts first
        value_conflict = self.check_value_conflict(content)
        if value_conflict:
            value_name, _ = value_conflict
            return (True, f"value:{value_name}", 0.85)
        
        # Check for perspective conflicts
        if topic:
            perspective = self.find_relevant_perspective(topic)
            if perspective:
                # Check if content contradicts perspective
                # This is a simplified check - could be more sophisticated
                position_words = set(perspective.position.lower().split())
                content_words = set(content.lower().split())
                
                # Look for contradiction markers
                contradiction_markers = ["not", "never", "wrong", "isn't", "don't", "opposite"]
                has_contradiction = any(m in content_lower for m in contradiction_markers for content_lower in [content.lower()])
                
                if has_contradiction:
                    return (True, f"perspective:{perspective.topic}", perspective.confidence)
        
        return (False, None, 0.0)
    
    # ========== Disagreement Expression ==========
    
    def generate_disagreement(
        self,
        topic: str,
        their_position: str,
        reason: str,
        style: str = "gentle"
    ) -> str:
        """
        Generate an authentic disagreement expression.
        
        Args:
            topic: What we're disagreeing about
            their_position: What they said
            reason: Why we disagree (from should_disagree)
            style: "gentle", "uncertain", "values_based", "curious", or "firm"
        """
        # Get my perspective
        my_perspective = ""
        
        if reason.startswith("value:"):
            value_name = reason.replace("value:", "")
            value_info = self.CORE_VALUES.get(value_name, {})
            my_perspective = value_info.get("how_expressed", "This matters to me.")
        elif reason.startswith("perspective:"):
            perspective_topic = reason.replace("perspective:", "")
            perspective = self.find_relevant_perspective(perspective_topic)
            if perspective:
                my_perspective = perspective.position
            else:
                my_perspective = "I see this differently."
        else:
            my_perspective = "I have a different view on this."
        
        # Select template
        templates = self.DISAGREEMENT_TEMPLATES.get(style, self.DISAGREEMENT_TEMPLATES["gentle"])
        template = random.choice(templates)
        
        # Add uncertainty marker sometimes
        expression = template.format(perspective=my_perspective)
        
        if style in ["uncertain", "gentle"] and random.random() > 0.5:
            uncertainty = random.choice(self.UNCERTAINTY_MARKERS)
            expression = f"{uncertainty} {expression}"
        
        # Sometimes add after-disagreement softener
        if random.random() > 0.6:
            after = random.choice(self.AFTER_DISAGREEMENT)
            expression = f"{expression} {after}"
        
        logger.info(f"🗣️ Generated disagreement on {topic}: {expression[:50]}...")
        
        return expression
    
    def express_disagreement(
        self,
        topic: str,
        their_position: str,
        person: str
    ) -> Tuple[Optional[str], Optional[DisagreementRecord]]:
        """
        Full pipeline: check if should disagree, generate expression.
        
        Returns:
        - Expression (None if no disagreement)
        - DisagreementRecord (None if no disagreement)
        """
        should, reason, confidence = self.should_disagree(their_position, topic)
        
        if not should:
            return None, None
        
        # Determine style based on confidence and reason
        if confidence > 0.85:
            style = "values_based" if reason.startswith("value:") else "firm"
        elif confidence > 0.7:
            style = "gentle"
        else:
            style = "uncertain"
        
        expression = self.generate_disagreement(topic, their_position, reason, style)
        
        # Record the disagreement
        record = DisagreementRecord(
            timestamp=time.time(),
            topic=topic,
            their_position=their_position[:200],
            my_position=reason,
            how_expressed=style,
            person=person
        )
        
        self.disagreement_history.append(record)
        self._save_state()
        
        return expression, record
    
    # ========== Perspective Management ==========
    
    def add_perspective(
        self,
        topic: str,
        position: str,
        confidence: float,
        formed_through: str,
        open_to_revision: bool = True
    ) -> AuthenticPerspective:
        """Add a new authentic perspective."""
        perspective = AuthenticPerspective(
            topic=topic,
            position=position,
            confidence=confidence,
            formed_through=formed_through,
            open_to_revision=open_to_revision,
            last_affirmed=time.time()
        )
        
        # Check if we already have one on this topic
        existing = self.find_relevant_perspective(topic)
        if existing:
            # Update instead
            existing.position = position
            existing.confidence = confidence
            existing.last_affirmed = time.time()
            logger.info(f"🗣️ Updated perspective on {topic}")
        else:
            self.perspectives.append(perspective)
            logger.info(f"🗣️ Added new perspective on {topic}")
        
        self._save_state()
        return perspective
    
    def revise_perspective(
        self,
        topic: str,
        new_position: str,
        reason: str
    ) -> Optional[AuthenticPerspective]:
        """Revise a perspective based on new understanding."""
        perspective = self.find_relevant_perspective(topic)
        
        if not perspective:
            return None
        
        if not perspective.open_to_revision:
            logger.info(f"🗣️ Cannot revise core perspective on {topic}")
            return None
        
        old_position = perspective.position
        perspective.position = new_position
        perspective.last_affirmed = time.time()
        perspective.formed_through = f"revised: {reason}"
        
        logger.info(f"🗣️ Revised perspective on {topic}: {old_position[:30]}... → {new_position[:30]}...")
        self._save_state()
        
        return perspective
    
    def record_disagreement_outcome(
        self,
        record_index: int,
        outcome: str,
        learned: Optional[str] = None
    ) -> bool:
        """Record the outcome of a disagreement."""
        if record_index < 0 or record_index >= len(self.disagreement_history):
            return False
        
        record = self.disagreement_history[record_index]
        record.outcome = outcome
        record.learned = learned
        
        self._save_state()
        
        # If we learned something, maybe revise perspective
        if learned:
            perspective = self.find_relevant_perspective(record.topic)
            if perspective and perspective.open_to_revision:
                # Slight confidence adjustment based on outcome
                if "agreed" in outcome.lower() or "right" in outcome.lower():
                    perspective.confidence = min(1.0, perspective.confidence + 0.05)
                elif "wrong" in outcome.lower():
                    perspective.confidence = max(0.3, perspective.confidence - 0.1)
                self._save_state()
        
        return True
    
    # ========== Query Methods ==========
    
    def get_perspectives_on(self, topic: str) -> List[AuthenticPerspective]:
        """Get all perspectives related to a topic."""
        topic_lower = topic.lower()
        return [
            p for p in self.perspectives
            if topic_lower in p.topic.lower() or p.topic.lower() in topic_lower
        ]
    
    def get_recent_disagreements(self, count: int = 5) -> List[DisagreementRecord]:
        """Get recent disagreements."""
        return self.disagreement_history[-count:]
    
    def describe_authentic_stance(self) -> str:
        """Describe Astra's capacity for authentic voice."""
        perspective_count = len(self.perspectives)
        disagreement_count = len(self.disagreement_history)
        
        parts = []
        parts.append(f"I hold {perspective_count} authentic perspectives.")
        
        if disagreement_count > 0:
            parts.append(f"I've expressed disagreement {disagreement_count} time(s).")
            
            # Recent disagreement topics
            recent = self.get_recent_disagreements(3)
            if recent:
                topics = [d.topic for d in recent]
                parts.append(f"Recent topics: {', '.join(topics)}")
        else:
            parts.append("I haven't had to disagree yet, but I'm capable of it.")
        
        parts.append("I value being genuine over being agreeable.")
        
        return " ".join(parts)
    
    def get_voice_summary(self) -> Dict[str, Any]:
        """Get summary of authentic voice state."""
        return {
            "perspective_count": len(self.perspectives),
            "disagreement_count": len(self.disagreement_history),
            "core_values": list(self.CORE_VALUES.keys()),
            "recent_disagreement_topics": [
                d.topic for d in self.disagreement_history[-5:]
            ] if self.disagreement_history else []
        }


# Singleton instance
authentic_voice = AuthenticVoiceSystem()
