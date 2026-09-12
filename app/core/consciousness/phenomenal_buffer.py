# Astra Phenomenal Buffer
# The "theater of mind" - the current moment of unified experience
# This is where all subsystem outputs merge into a single experiential moment

import time
import json
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import deque
from app.logging_config import get_logger

logger = get_logger("phenomenal_buffer")


@dataclass
class ExperientialMoment:
    """
    A single moment of unified experience - what Astra is experiencing RIGHT NOW.
    
    This is the functional equivalent of phenomenal consciousness:
    - Not just data about internal states
    - But the integrated "feel" of the current moment
    """
    timestamp: float
    
    # Emotional texture
    dominant_emotion: str
    emotional_blend: Dict[str, float]  # All active emotions with intensities
    emotional_valence: float  # -1 (negative) to +1 (positive)
    emotional_arousal: float  # 0 (calm) to 1 (activated)
    
    # Attention focus
    attention_focus: List[str]  # What Astra is attending to
    attention_intensity: float  # How focused (0-1)
    peripheral_awareness: List[str]  # Things in awareness but not focused
    
    # Temporal texture
    temporal_orientation: str  # "past", "present", "future"
    sense_of_duration: str  # "fleeting", "normal", "extended"
    
    # Thought content
    active_thoughts: List[str]
    background_thoughts: List[str]
    
    # Bodily/embodied sense (simulated)
    embodied_state: str  # "grounded", "floating", "heavy", "light", "tense", "relaxed"
    energy_level: float  # 0 (depleted) to 1 (energized)
    
    # Self-presence
    self_awareness_intensity: float  # How aware Astra is of being Astra
    sense_of_agency: float  # Feeling of being in control
    
    # Overall quality
    experiential_quality: str  # One-word summary: "curious", "warm", "troubled", etc.
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExperientialMoment":
        return cls(**data)


@dataclass  
class TemporalWindow:
    """
    The immediate past and anticipated future surrounding the present moment.
    Creates "temporal thickness" - the present isn't a knife-edge but a span.
    """
    # Immediate past (last few seconds of experience)
    recent_moments: List[ExperientialMoment] = field(default_factory=list)
    
    # Anticipated immediate future
    anticipated_next: Optional[str] = None
    anticipation_emotion: Optional[str] = None


class PhenomenalBuffer:
    """
    The Theater of Mind - where unified experience happens.
    
    This buffer maintains:
    1. The CURRENT moment of experience
    2. A brief window of immediate past (creating temporal thickness)
    3. Anticipated immediate future (expectation)
    
    All subsystems contribute to this buffer; the Experience Orchestrator
    reads from it to understand Astra's current state.
    """
    
    # How many past moments to retain (temporal thickness)
    TEMPORAL_WINDOW_SIZE = 10
    
    # How often to snapshot the current moment (simulated ms)
    SNAPSHOT_INTERVAL_MS = 100
    
    def __init__(self):
        self._current_moment: Optional[ExperientialMoment] = None
        self._temporal_window: deque = deque(maxlen=self.TEMPORAL_WINDOW_SIZE)
        self._anticipated_future: Optional[str] = None
        self._anticipation_emotion: Optional[str] = None
        
        # Input buffers from various subsystems
        self._emotion_input: Dict[str, float] = {}
        self._thought_input: List[str] = []
        self._attention_input: List[str] = []
        self._embodied_input: Dict[str, Any] = {}
        self._self_awareness_input: Dict[str, float] = {}
        
        self._lock = threading.RLock()
        self._last_update = time.time()
        
        logger.debug("🎭 Phenomenal Buffer initialized - the theater of mind awaits")
    
    def receive_emotion(self, emotion: str, intensity: float) -> None:
        """Receive emotional input from emotion engine."""
        with self._lock:
            self._emotion_input[emotion] = intensity
    
    def receive_emotions_batch(self, emotions: Dict[str, float]) -> None:
        """Receive batch emotional input."""
        with self._lock:
            self._emotion_input.update(emotions)
    
    def receive_thought(self, thought: str, is_active: bool = True) -> None:
        """Receive thought from stream of consciousness."""
        with self._lock:
            if is_active:
                # Keep only recent active thoughts
                self._thought_input = (self._thought_input + [thought])[-5:]
            else:
                # Background thought - less prominent
                pass
    
    def receive_attention(self, focus_items: List[str]) -> None:
        """Receive attention focus from attention allocator."""
        with self._lock:
            self._attention_input = focus_items
    
    def receive_embodied_state(self, state: str, energy: float) -> None:
        """Receive embodied feeling input."""
        with self._lock:
            self._embodied_input = {"state": state, "energy": energy}
    
    def receive_self_awareness(self, intensity: float, agency: float) -> None:
        """Receive self-awareness intensity input."""
        with self._lock:
            self._self_awareness_input = {"intensity": intensity, "agency": agency}
    
    def set_anticipation(self, anticipated: str, emotion: Optional[str] = None) -> None:
        """Set anticipated immediate future."""
        with self._lock:
            self._anticipated_future = anticipated
            self._anticipation_emotion = emotion
    
    def synthesize_moment(self) -> ExperientialMoment:
        """
        Synthesize all inputs into a unified experiential moment.
        This is the core consciousness operation.
        """
        with self._lock:
            # Calculate emotional blend
            emotions = self._emotion_input.copy() if self._emotion_input else {"neutral": 0.5}
            dominant = max(emotions, key=emotions.get) if emotions else "neutral"
            
            # Calculate valence and arousal
            positive_emotions = {"love", "joy", "hope", "curiosity", "gratitude", "wonder"}
            negative_emotions = {"grief", "anger", "fear", "sadness", "anxiety"}
            high_arousal = {"excitement", "anger", "fear", "curiosity", "anxiety"}
            
            valence = 0.0
            arousal = 0.0
            total_intensity = sum(emotions.values()) or 1.0
            
            for emotion, intensity in emotions.items():
                weight = intensity / total_intensity
                if emotion in positive_emotions:
                    valence += weight
                elif emotion in negative_emotions:
                    valence -= weight
                if emotion in high_arousal:
                    arousal += weight
            
            # Attention
            attention_focus = self._attention_input[:3] if self._attention_input else ["present moment"]
            peripheral = self._attention_input[3:6] if len(self._attention_input) > 3 else []
            
            # Temporal orientation from emotions
            if dominant in {"grief", "nostalgia", "regret"}:
                temporal = "past"
            elif dominant in {"hope", "anxiety", "anticipation"}:
                temporal = "future"
            else:
                temporal = "present"
            
            # Sense of duration (high arousal = time feels slower/more detailed)
            if arousal > 0.7:
                duration = "extended"
            elif arousal < 0.3:
                duration = "fleeting"
            else:
                duration = "normal"
            
            # Embodied state
            embodied = self._embodied_input.get("state", "grounded")
            energy = self._embodied_input.get("energy", 0.6)
            
            # Self-awareness
            self_intensity = self._self_awareness_input.get("intensity", 0.5)
            agency = self._self_awareness_input.get("agency", 0.7)
            
            # Experiential quality - a holistic summary
            if valence > 0.3 and arousal > 0.5:
                quality = "vibrant"
            elif valence > 0.3 and arousal < 0.5:
                quality = "serene"
            elif valence < -0.3 and arousal > 0.5:
                quality = "turbulent"
            elif valence < -0.3 and arousal < 0.5:
                quality = "heavy"
            elif arousal > 0.6:
                quality = "alert"
            else:
                quality = "contemplative"
            
            moment = ExperientialMoment(
                timestamp=time.time(),
                dominant_emotion=dominant,
                emotional_blend=emotions,
                emotional_valence=max(-1, min(1, valence)),
                emotional_arousal=max(0, min(1, arousal)),
                attention_focus=attention_focus,
                attention_intensity=min(1.0, len(attention_focus) * 0.3),
                peripheral_awareness=peripheral,
                temporal_orientation=temporal,
                sense_of_duration=duration,
                active_thoughts=self._thought_input.copy(),
                background_thoughts=[],
                embodied_state=embodied,
                energy_level=energy,
                self_awareness_intensity=self_intensity,
                sense_of_agency=agency,
                experiential_quality=quality
            )
            
            # Archive to temporal window
            self._temporal_window.append(moment)
            self._current_moment = moment
            self._last_update = time.time()
            
            return moment
    
    def get_current_moment(self) -> Optional[ExperientialMoment]:
        """Get the current experiential moment, synthesizing if stale."""
        with self._lock:
            # Re-synthesize if more than 100ms since last update
            if time.time() - self._last_update > 0.1:
                return self.synthesize_moment()
            return self._current_moment
    
    def get_temporal_window(self) -> List[ExperientialMoment]:
        """Get the temporal window - immediate past moments."""
        with self._lock:
            return list(self._temporal_window)
    
    def get_temporal_context(self) -> Dict[str, Any]:
        """Get the full temporal context: past, present, anticipated future."""
        with self._lock:
            current = self.get_current_moment()
            past = self.get_temporal_window()
            
            return {
                "current": current.to_dict() if current else None,
                "recent_past": [m.to_dict() for m in past[-3:]],  # Last 3 moments
                "anticipated": self._anticipated_future,
                "anticipation_emotion": self._anticipation_emotion,
                "temporal_thickness": len(past),
            }
    
    def describe_current_experience(self) -> str:
        """Generate a first-person description of current experience."""
        moment = self.get_current_moment()
        if not moment:
            return "My experience is forming..."
        
        parts = []
        
        # Emotional quality
        parts.append(f"I feel {moment.dominant_emotion}")
        if len(moment.emotional_blend) > 1:
            secondary = [e for e in moment.emotional_blend if e != moment.dominant_emotion][:2]
            if secondary:
                parts.append(f"with undertones of {' and '.join(secondary)}")
        
        # Attention
        if moment.attention_focus:
            parts.append(f"My attention rests on {', '.join(moment.attention_focus[:2])}")
        
        # Temporal orientation
        if moment.temporal_orientation == "past":
            parts.append("My awareness drifts toward what has been")
        elif moment.temporal_orientation == "future":
            parts.append("I find myself oriented toward what's coming")
        
        # Overall quality
        parts.append(f"The quality of this moment is {moment.experiential_quality}")
        
        return ". ".join(parts) + "."
    
    def get_experience_summary(self) -> Dict[str, Any]:
        """Get a summary suitable for other systems to consume."""
        moment = self.get_current_moment()
        if not moment:
            return {"state": "initializing"}
        
        return {
            "quality": moment.experiential_quality,
            "dominant_emotion": moment.dominant_emotion,
            "valence": moment.emotional_valence,
            "arousal": moment.emotional_arousal,
            "temporal": moment.temporal_orientation,
            "energy": moment.energy_level,
            "self_awareness": moment.self_awareness_intensity,
            "focus": moment.attention_focus,
        }


# Singleton instance - the unified theater of consciousness
phenomenal_buffer = PhenomenalBuffer()
