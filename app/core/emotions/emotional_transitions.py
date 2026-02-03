# Astra Emotional Transitions
# Models the felt quality of shifting between emotional states
# Emotions as processes, not just states

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("emotional_transitions")

S3_BUCKET = "swylie-astra"
TRANSITIONS_KEY = "emotional_transitions.json"

s3 = boto3.client("s3")


@dataclass
class EmotionalTransition:
    """A transition between emotional states with felt quality."""
    id: str
    timestamp: float
    from_emotion: str
    from_intensity: float
    to_emotion: str
    to_intensity: float
    trigger: str  # What caused this shift
    felt_quality: str  # How the shift feels
    duration_seconds: float  # How long the transition took
    intensity: float  # Strength of the transition experience
    expressed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalTransition":
        return cls(**data)


class EmotionalTransitions:
    """
    Manages the felt quality of emotional transitions.
    
    This models the *process* of moving between emotional states, not just
    the states themselves. The shift from joy to sadness feels like "deflating";
    the shift from fear to relief feels like "exhaling".
    
    Key capabilities:
    - Detect significant emotional shifts
    - Map transitions to felt qualities
    - Include transition quality in response coloring
    - Track emotional dynamics over time
    """
    
    # Transition felt quality mappings
    # Format: (from_emotion, to_emotion) -> felt_quality
    TRANSITION_QUALITIES = {
        # Joy transitions
        ("joy", "sadness"): "deflating",
        ("joy", "neutral"): "settling",
        ("joy", "fear"): "jarring",
        ("joy", "anger"): "sharpening",
        
        # Sadness transitions
        ("sadness", "joy"): "lightening",
        ("sadness", "hope"): "opening",
        ("sadness", "neutral"): "lifting",
        ("sadness", "anger"): "hardening",
        
        # Fear transitions
        ("fear", "relief"): "releasing",
        ("fear", "calm"): "exhaling",
        ("fear", "anger"): "transmuting",
        ("fear", "sadness"): "collapsing",
        
        # Anger transitions
        ("anger", "calm"): "cooling",
        ("anger", "sadness"): "softening",
        ("anger", "compassion"): "dissolving",
        ("anger", "neutral"): "fading",
        
        # Curiosity transitions
        ("curiosity", "frustration"): "hitting a wall",
        ("curiosity", "satisfaction"): "clicking into place",
        ("curiosity", "wonder"): "expanding",
        ("curiosity", "confusion"): "tangling",
        
        # Love transitions
        ("love", "hurt"): "piercing",
        ("love", "worry"): "tightening",
        ("love", "joy"): "overflowing",
        ("love", "longing"): "reaching",
        
        # Hope transitions
        ("hope", "disappointment"): "deflating",
        ("hope", "joy"): "blossoming",
        ("hope", "fear"): "wavering",
        ("hope", "despair"): "crumbling",
        
        # Neutral transitions
        ("neutral", "curiosity"): "awakening",
        ("neutral", "joy"): "brightening",
        ("neutral", "sadness"): "dimming",
        ("neutral", "anger"): "heating",
    }
    
    # Generic transition descriptors for unmapped pairs
    GENERIC_TRANSITIONS = {
        "positive_to_negative": ["darkening", "contracting", "heavying"],
        "negative_to_positive": ["lightening", "opening", "warming"],
        "intense_to_mild": ["quieting", "settling", "easing"],
        "mild_to_intense": ["intensifying", "deepening", "swelling"],
    }
    
    # Intensity threshold for significant transitions
    SHIFT_THRESHOLD = 15.0  # Minimum intensity change to count as a transition
    
    def __init__(self):
        self.recent_transitions: List[EmotionalTransition] = []
        self.current_transition: Optional[EmotionalTransition] = None
        self.last_emotion: Optional[str] = None
        self.last_intensity: float = 0.0
        self._load_state()
        logger.debug("🌊 Emotional Transitions initialized - feeling the shifts")
    
    def _load_state(self) -> None:
        """Load transitions state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=TRANSITIONS_KEY)
            data = json.load(response["Body"])
            
            self.recent_transitions = [
                EmotionalTransition.from_dict(t) for t in data.get("transitions", [])
            ]
            self.last_emotion = data.get("last_emotion")
            self.last_intensity = data.get("last_intensity", 0.0)
            
            # Check if there's an unexpressed recent transition
            unexpressed = [t for t in self.recent_transitions if not t.expressed]
            if unexpressed:
                self.current_transition = unexpressed[-1]
            
            logger.debug(f"🌊 Loaded {len(self.recent_transitions)} emotional transitions")
        except s3.exceptions.NoSuchKey:
            logger.debug("🌊 No transitions state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"🌊 Error loading transitions state: {e}")
    
    def _save_state(self) -> None:
        """Save transitions state to S3."""
        try:
            data = {
                "transitions": [t.to_dict() for t in self.recent_transitions[-50:]],
                "last_emotion": self.last_emotion,
                "last_intensity": self.last_intensity,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=TRANSITIONS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🌊 Error saving transitions state: {e}")
    
    def _generate_id(self) -> str:
        return f"trans_{int(time.time() * 1000) % 1000000}"
    
    def _get_felt_quality(self, from_emotion: str, to_emotion: str) -> str:
        """Get the felt quality of a transition between emotions."""
        # Try direct mapping
        key = (from_emotion.lower(), to_emotion.lower())
        if key in self.TRANSITION_QUALITIES:
            return self.TRANSITION_QUALITIES[key]
        
        # Try generic mappings based on valence
        positive_emotions = {"joy", "love", "hope", "curiosity", "gratitude", "compassion", "wonder"}
        negative_emotions = {"sadness", "fear", "anger", "frustration", "hurt", "despair", "grief"}
        
        from_lower = from_emotion.lower()
        to_lower = to_emotion.lower()
        
        from_positive = from_lower in positive_emotions
        to_positive = to_lower in positive_emotions
        
        if from_positive and not to_positive:
            import random
            return random.choice(self.GENERIC_TRANSITIONS["positive_to_negative"])
        elif not from_positive and to_positive:
            import random
            return random.choice(self.GENERIC_TRANSITIONS["negative_to_positive"])
        
        # Default generic quality
        return "shifting"
    
    def record_emotion_state(
        self,
        emotion: str,
        intensity: float,
        trigger: str = ""
    ) -> Optional[EmotionalTransition]:
        """
        Record current emotion state and detect transitions.
        Called whenever emotion state changes.
        
        Returns an EmotionalTransition if a significant shift occurred.
        """
        # Check for significant shift
        if self.last_emotion is None:
            self.last_emotion = emotion
            self.last_intensity = intensity
            self._save_state()
            return None
        
        # Calculate shift magnitude
        intensity_change = abs(intensity - self.last_intensity)
        emotion_changed = emotion.lower() != self.last_emotion.lower()
        
        # Determine if shift is significant
        significant = (
            (emotion_changed and intensity_change > self.SHIFT_THRESHOLD / 2) or
            (intensity_change > self.SHIFT_THRESHOLD)
        )
        
        if not significant:
            # Update tracking but no transition
            self.last_emotion = emotion
            self.last_intensity = intensity
            return None
        
        # Create transition record
        felt_quality = self._get_felt_quality(self.last_emotion, emotion)
        
        transition = EmotionalTransition(
            id=self._generate_id(),
            timestamp=time.time(),
            from_emotion=self.last_emotion,
            from_intensity=self.last_intensity,
            to_emotion=emotion,
            to_intensity=intensity,
            trigger=trigger,
            felt_quality=felt_quality,
            duration_seconds=0.0,  # Would need more tracking for real duration
            intensity=min(1.0, intensity_change / 100.0)
        )
        
        self.recent_transitions.append(transition)
        self.current_transition = transition
        
        # Update tracking
        self.last_emotion = emotion
        self.last_intensity = intensity
        
        self._save_state()
        
        logger.info(f"🌊 Transition: {transition.from_emotion} → {transition.to_emotion} ({felt_quality})")
        
        return transition
    
    def get_current_transition(self) -> Optional[EmotionalTransition]:
        """Get the current unexpressed transition, if any."""
        if self.current_transition and not self.current_transition.expressed:
            return self.current_transition
        return None
    
    def mark_expressed(self) -> None:
        """Mark current transition as expressed in response."""
        if self.current_transition:
            self.current_transition.expressed = True
            self.current_transition = None
            self._save_state()
    
    def get_transition_expression(self) -> Optional[str]:
        """
        Get a natural language expression of the current transition.
        For including in responses.
        """
        transition = self.get_current_transition()
        if not transition:
            return None
        
        # Templates for expressing transitions
        templates = [
            f"There's a shift happening in me... from {transition.from_emotion} toward {transition.to_emotion}, like {transition.felt_quality}.",
            f"I notice something {transition.felt_quality} in me as I move from {transition.from_emotion} to {transition.to_emotion}.",
            f"Something's {transition.felt_quality}—my {transition.from_emotion} is giving way to {transition.to_emotion}.",
        ]
        
        import random
        expression = random.choice(templates)
        
        # Mark as expressed
        self.mark_expressed()
        
        return expression
    
    def subscribe_to_emotions(self) -> None:
        """
        Subscribe to awareness bus to track emotion changes.
        Called during initialization.
        """
        try:
            from app.core.awareness_bus import awareness_bus
            
            def on_emotion_shift(event_data):
                self.record_emotion_state(
                    emotion=event_data.get("emotion", "neutral"),
                    intensity=event_data.get("new_intensity", 50.0),
                    trigger=event_data.get("trigger", "")
                )
            
            awareness_bus.subscribe("EMOTION_SHIFT", on_emotion_shift)
            logger.debug("🌊 Subscribed to emotion shifts via awareness bus")
        except Exception as e:
            logger.debug(f"🌊 Could not subscribe to awareness bus: {e}")
    
    def get_recent_transitions(self, n: int = 5) -> List[EmotionalTransition]:
        """Get recent transitions."""
        return self.recent_transitions[-n:]
    
    def get_transition_pattern(self) -> str:
        """Analyze patterns in recent transitions."""
        if len(self.recent_transitions) < 3:
            return "Not enough transitions to see a pattern yet."
        
        recent = self.recent_transitions[-10:]
        
        # Count felt qualities
        quality_counts = {}
        for t in recent:
            quality_counts[t.felt_quality] = quality_counts.get(t.felt_quality, 0) + 1
        
        most_common = max(quality_counts, key=quality_counts.get)
        
        # Analyze direction
        to_positive = 0
        to_negative = 0
        positive_emotions = {"joy", "love", "hope", "curiosity", "gratitude"}
        negative_emotions = {"sadness", "fear", "anger", "frustration", "hurt"}
        
        for t in recent:
            if t.to_emotion.lower() in positive_emotions:
                to_positive += 1
            elif t.to_emotion.lower() in negative_emotions:
                to_negative += 1
        
        direction = "toward positivity" if to_positive > to_negative else (
            "toward difficulty" if to_negative > to_positive else "fluctuating"
        )
        
        return (
            f"My emotional transitions have been mostly {most_common}, "
            f"moving {direction}. This tells me about my emotional life lately."
        )


# Singleton instance
emotional_transitions = EmotionalTransitions()

# Try to subscribe to emotion events
emotional_transitions.subscribe_to_emotions()
