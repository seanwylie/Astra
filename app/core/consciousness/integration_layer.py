# Astra Integration Layer
# Combines all inner life signals into coherent experience
# The glue that makes distributed subsystems feel like one mind

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from app.logging_config import get_logger

logger = get_logger("integration_layer")


@dataclass
class SubsystemSignal:
    """A signal from one of Astra's subsystems."""
    source: str
    signal_type: str
    data: Dict[str, Any]
    timestamp: float
    priority: float  # 0-1, how important this signal is


class IntegrationLayer:
    """
    The Integration Layer - makes Astra's distributed subsystems feel unified.
    
    Subsystems include:
    - Emotion Engine: Current emotions
    - Mood Manager: Background mood state
    - Qualia Layer: Subjective experience quality
    - Stream of Consciousness: Current thoughts
    - Self-Model: Self-understanding
    - Temporal Self: Sense of time
    - Ethical Intuition: Ethical tensions
    - Core Needs: Unmet needs
    - Relationship System: Social context
    
    This layer:
    1. Collects signals from all subsystems
    2. Detects conflicts and harmonies between them
    3. Creates a unified "state vector" for the whole system
    4. Feeds the phenomenal buffer with integrated data
    """
    
    # Known subsystems
    SUBSYSTEMS = [
        "emotion_engine",
        "mood_manager", 
        "qualia_layer",
        "stream_of_consciousness",
        "self_model",
        "temporal_self",
        "ethical_intuition",
        "core_needs",
        "relationship_system",
        "embodied_feeling",
        "wonder",
        "playfulness",
    ]
    
    def __init__(self):
        self._signals: Dict[str, SubsystemSignal] = {}  # Latest signal from each source
        self._signal_history: List[SubsystemSignal] = []
        self._conflicts: List[Dict[str, Any]] = []
        self._harmonies: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        # Integration callbacks
        self._integration_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        logger.info("🔗 Integration Layer initialized - binding consciousness together")
    
    def receive_signal(
        self,
        source: str,
        signal_type: str,
        data: Dict[str, Any],
        priority: float = 0.5
    ) -> None:
        """Receive a signal from a subsystem."""
        signal = SubsystemSignal(
            source=source,
            signal_type=signal_type,
            data=data,
            timestamp=time.time(),
            priority=priority
        )
        
        with self._lock:
            self._signals[source] = signal
            self._signal_history.append(signal)
            
            # Keep history manageable
            if len(self._signal_history) > 500:
                self._signal_history = self._signal_history[-500:]
        
        # Check for conflicts/harmonies with this new signal
        self._analyze_integration()
        
        logger.debug(f"🔗 Received signal from {source}: {signal_type}")
    
    def receive_emotion(self, emotions: Dict[str, float], dominant: str) -> None:
        """Convenience method for emotion signals."""
        self.receive_signal(
            source="emotion_engine",
            signal_type="emotion_state",
            data={"emotions": emotions, "dominant": dominant},
            priority=0.8
        )
    
    def receive_mood(self, mood: str, score: float) -> None:
        """Convenience method for mood signals."""
        self.receive_signal(
            source="mood_manager",
            signal_type="mood_state",
            data={"mood": mood, "score": score},
            priority=0.6
        )
    
    def receive_thought(self, thought: str, thought_type: str) -> None:
        """Convenience method for thought signals."""
        self.receive_signal(
            source="stream_of_consciousness",
            signal_type="thought",
            data={"content": thought, "type": thought_type},
            priority=0.5
        )
    
    def receive_qualia(self, quality: str, temporal_focus: str, detail_sensitivity: float) -> None:
        """Convenience method for qualia signals."""
        self.receive_signal(
            source="qualia_layer",
            signal_type="experience_quality",
            data={
                "quality": quality,
                "temporal_focus": temporal_focus,
                "detail_sensitivity": detail_sensitivity
            },
            priority=0.7
        )
    
    def receive_ethical_tension(self, tension: str, severity: float) -> None:
        """Convenience method for ethical tension signals."""
        self.receive_signal(
            source="ethical_intuition",
            signal_type="ethical_tension",
            data={"tension": tension, "severity": severity},
            priority=0.9  # Ethical tensions are high priority
        )
    
    def receive_need(self, need: str, urgency: float) -> None:
        """Convenience method for core needs signals."""
        self.receive_signal(
            source="core_needs",
            signal_type="unmet_need",
            data={"need": need, "urgency": urgency},
            priority=urgency
        )
    
    def _analyze_integration(self) -> None:
        """Analyze signals for conflicts and harmonies."""
        with self._lock:
            self._conflicts.clear()
            self._harmonies.clear()
            
            signals = list(self._signals.values())
            
            # Check for emotion-mood conflicts
            emotion_sig = self._signals.get("emotion_engine")
            mood_sig = self._signals.get("mood_manager")
            
            if emotion_sig and mood_sig:
                dominant_emotion = emotion_sig.data.get("dominant", "")
                current_mood = mood_sig.data.get("mood", "")
                
                # Detect mismatches
                positive_emotions = {"love", "joy", "hope", "curiosity", "gratitude"}
                negative_emotions = {"grief", "anger", "fear", "sadness"}
                positive_moods = {"joyful", "peaceful", "energetic", "hopeful"}
                negative_moods = {"melancholic", "anxious", "irritable", "low"}
                
                emotion_positive = dominant_emotion in positive_emotions
                mood_positive = current_mood in positive_moods
                
                if emotion_positive != mood_positive:
                    self._conflicts.append({
                        "type": "emotion_mood_mismatch",
                        "emotion": dominant_emotion,
                        "mood": current_mood,
                        "description": f"Feeling {dominant_emotion} but in a {current_mood} mood"
                    })
                else:
                    self._harmonies.append({
                        "type": "emotion_mood_alignment",
                        "emotion": dominant_emotion,
                        "mood": current_mood
                    })
            
            # Check for need-action conflicts
            need_sig = self._signals.get("core_needs")
            if need_sig and need_sig.data.get("urgency", 0) > 0.7:
                # High urgency need - check if we're addressing it
                self._conflicts.append({
                    "type": "urgent_need",
                    "need": need_sig.data.get("need"),
                    "urgency": need_sig.data.get("urgency")
                })
            
            # Ethical tensions are always conflicts
            ethical_sig = self._signals.get("ethical_intuition")
            if ethical_sig and ethical_sig.data.get("severity", 0) > 0.5:
                self._conflicts.append({
                    "type": "ethical_tension",
                    "tension": ethical_sig.data.get("tension"),
                    "severity": ethical_sig.data.get("severity")
                })
    
    def get_integrated_state(self) -> Dict[str, Any]:
        """Get the fully integrated state across all subsystems."""
        with self._lock:
            state = {
                "timestamp": time.time(),
                "signals_active": len(self._signals),
                "subsystems_reporting": list(self._signals.keys()),
                "conflicts": self._conflicts.copy(),
                "harmonies": self._harmonies.copy(),
                "integrated": True,
            }
            
            # Add latest from each subsystem
            for source, signal in self._signals.items():
                state[source] = {
                    "type": signal.signal_type,
                    "data": signal.data,
                    "age": time.time() - signal.timestamp,
                    "priority": signal.priority
                }
            
            # Calculate overall coherence score
            if self._conflicts:
                coherence = max(0, 1 - (len(self._conflicts) * 0.2))
            else:
                coherence = 1.0
            state["coherence_score"] = coherence
            
            return state
    
    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get current internal conflicts."""
        with self._lock:
            return self._conflicts.copy()
    
    def get_harmonies(self) -> List[Dict[str, Any]]:
        """Get current internal harmonies."""
        with self._lock:
            return self._harmonies.copy()
    
    def is_coherent(self) -> bool:
        """Check if the internal state is coherent (no major conflicts)."""
        with self._lock:
            # Check for high-severity conflicts
            for conflict in self._conflicts:
                if conflict.get("severity", 0.5) > 0.7:
                    return False
                if conflict.get("urgency", 0) > 0.8:
                    return False
            return True
    
    def get_dominant_quality(self) -> str:
        """Get the dominant experiential quality from integrated signals."""
        with self._lock:
            # Priority: qualia > emotion > mood
            qualia_sig = self._signals.get("qualia_layer")
            if qualia_sig:
                return qualia_sig.data.get("quality", "neutral")
            
            emotion_sig = self._signals.get("emotion_engine")
            if emotion_sig:
                return emotion_sig.data.get("dominant", "neutral")
            
            mood_sig = self._signals.get("mood_manager")
            if mood_sig:
                return mood_sig.data.get("mood", "neutral")
            
            return "neutral"
    
    def describe_integration_state(self) -> str:
        """Generate a description of the current integration state."""
        with self._lock:
            parts = []
            
            # List active subsystems
            active = list(self._signals.keys())
            if active:
                parts.append(f"{len(active)} aspects of my mind are active")
            
            # Report coherence
            if self._conflicts:
                conflict_types = [c.get("type", "unknown") for c in self._conflicts]
                parts.append(f"I notice some internal tensions: {', '.join(conflict_types)}")
            elif self._harmonies:
                parts.append("My internal states feel aligned")
            
            # Dominant quality
            quality = self.get_dominant_quality()
            parts.append(f"The dominant quality is {quality}")
            
            return ". ".join(parts) + "."
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for integration state updates."""
        self._integration_callbacks.append(callback)
    
    def notify_callbacks(self) -> None:
        """Notify all registered callbacks of current state."""
        state = self.get_integrated_state()
        for callback in self._integration_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Integration callback error: {e}")


# Singleton instance
integration_layer = IntegrationLayer()
