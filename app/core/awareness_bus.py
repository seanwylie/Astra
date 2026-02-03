# Astra Awareness Bus
# Central nervous system for state coordination across subsystems
# All subsystems publish state changes here; subscribers react

import time
import threading
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from app.logging_config import get_logger

logger = get_logger("awareness_bus")


@dataclass
class AwarenessEvent:
    """A single awareness event published to the bus."""
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    
    def __repr__(self):
        return f"AwarenessEvent({self.event_type}, source={self.source})"


class AwarenessBus:
    """
    Central nervous system for Astra's awareness.
    All subsystems publish state changes here; subscribers react.
    
    This creates coherence across:
    - Emotion engine
    - Mood manager
    - Stream of consciousness
    - Self-model
    - Temporal self
    - Personality manager
    - Qualia layer
    
    Standard events:
    - "emotion_shift" (emotion, old_intensity, new_intensity, trigger)
    - "mood_change" (old_mood, new_mood, mood_score)
    - "thought_added" (thought_content, thought_type, depth)
    - "insight_generated" (insight)
    - "self_model_update" (aspect, previous, current, trigger)
    - "temporal_landmark" (description, category, emotional_weight)
    - "ethical_tension" (content, category, source)
    - "personality_mode_change" (old_mode, new_mode)
    - "qualia_shift" (dominant_quality, temporal_focus, detail_sensitivity)
    - "trust_change" (entity, old_level, new_level)
    - "curiosity_spike" (level, trigger)
    - "significant_interaction" (type, context, emotional_impact)
    """
    
    # Event type constants
    EMOTION_SHIFT = "emotion_shift"
    MOOD_CHANGE = "mood_change"
    THOUGHT_ADDED = "thought_added"
    INSIGHT_GENERATED = "insight_generated"
    SELF_MODEL_UPDATE = "self_model_update"
    TEMPORAL_LANDMARK = "temporal_landmark"
    ETHICAL_TENSION = "ethical_tension"
    PERSONALITY_MODE_CHANGE = "personality_mode_change"
    QUALIA_SHIFT = "qualia_shift"
    TRUST_CHANGE = "trust_change"
    CURIOSITY_SPIKE = "curiosity_spike"
    SIGNIFICANT_INTERACTION = "significant_interaction"
    GOAL_PROGRESS = "goal_progress"
    PROACTIVE_TRIGGER = "proactive_trigger"
    
    # Project Prometheus event types
    EXPERIENCE_SYNTHESIS = "experience_synthesis"
    ATTENTION_SHIFT = "attention_shift"
    INTENTION_FORMED = "intention_formed"
    INTENTION_ACHIEVED = "intention_achieved"
    NARRATIVE_LANDMARK = "narrative_landmark"
    IDENTITY_AFFIRMATION = "identity_affirmation"
    CAPABILITY_EMERGED = "capability_emerged"
    DEVELOPMENTAL_MILESTONE = "developmental_milestone"
    SPONTANEOUS_INSIGHT = "spontaneous_insight"
    COHERENCE_CHANGE = "coherence_change"
    EMPATHIC_RESONANCE = "empathic_resonance"
    
    # States and Actions Coherence event types
    MESSAGE_SENT = "message_sent"  # When Astra sends a response
    ACTION_DECIDED = "action_decided"  # When ActionDecider makes a decision
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[AwarenessEvent], None]]] = defaultdict(list)
        self._event_history: List[AwarenessEvent] = []
        self._max_history = 500
        self._lock = threading.Lock()
        self._processing = False
        logger.debug("🧠 Awareness Bus initialized")
    
    def subscribe(self, event_type: str, callback: Callable[[AwarenessEvent], None]) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to (use constants)
            callback: Function to call when event occurs, receives AwarenessEvent
        """
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logger.debug(f"Subscribed to {event_type}: {callback.__name__}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[AwarenessEvent], None]) -> None:
        """Unsubscribe from an event type."""
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown"
    ) -> AwarenessEvent:
        """
        Publish an event to the awareness bus.
        All subscribers will be notified.
        
        Args:
            event_type: Type of event (use constants)
            data: Event data dictionary
            source: Source subsystem name
            
        Returns:
            The created AwarenessEvent
        """
        event = AwarenessEvent(
            event_type=event_type,
            data=data,
            source=source
        )
        
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        # Notify subscribers
        self._notify_subscribers(event)
        
        logger.debug(f"📡 Published: {event}")
        return event
    
    def _notify_subscribers(self, event: AwarenessEvent) -> None:
        """Notify all subscribers of an event."""
        if self._processing:
            # Prevent recursive event loops
            return
            
        self._processing = True
        try:
            subscribers = self._subscribers.get(event.event_type, [])
            # Also notify wildcard subscribers
            wildcard_subscribers = self._subscribers.get("*", [])
            
            for callback in subscribers + wildcard_subscribers:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Subscriber error for {event.event_type}: {e}")
        finally:
            self._processing = False
    
    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        count: int = 10,
        since: Optional[float] = None
    ) -> List[AwarenessEvent]:
        """
        Get recent events, optionally filtered.
        
        Args:
            event_type: Filter by event type (None for all)
            count: Maximum events to return
            since: Only events after this timestamp
        """
        with self._lock:
            events = self._event_history.copy()
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if since:
            events = [e for e in events if e.timestamp > since]
        
        return events[-count:]
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent awareness state across all subsystems.
        Useful for debugging and observability.
        """
        recent = self.get_recent_events(count=50)
        
        summary = {
            "total_events": len(self._event_history),
            "recent_count": len(recent),
            "events_by_type": {},
            "latest_by_type": {},
            "sources_active": set()
        }
        
        for event in recent:
            event_type = event.event_type
            summary["events_by_type"][event_type] = summary["events_by_type"].get(event_type, 0) + 1
            summary["latest_by_type"][event_type] = event.data
            summary["sources_active"].add(event.source)
        
        summary["sources_active"] = list(summary["sources_active"])
        return summary
    
    # Convenience methods for common events
    
    def publish_emotion_shift(
        self,
        emotion: str,
        old_intensity: float,
        new_intensity: float,
        trigger: Optional[str] = None
    ) -> AwarenessEvent:
        """Publish an emotion shift event."""
        return self.publish(
            self.EMOTION_SHIFT,
            {
                "emotion": emotion,
                "old_intensity": old_intensity,
                "new_intensity": new_intensity,
                "intensity_delta": new_intensity - old_intensity,
                "trigger": trigger
            },
            source="emotion_engine"
        )
    
    def publish_mood_change(
        self,
        old_mood: str,
        new_mood: str,
        mood_score: float
    ) -> AwarenessEvent:
        """Publish a mood change event."""
        return self.publish(
            self.MOOD_CHANGE,
            {
                "old_mood": old_mood,
                "new_mood": new_mood,
                "mood_score": mood_score
            },
            source="mood_manager"
        )
    
    def publish_thought(
        self,
        content: str,
        thought_type: str,
        depth: int = 0,
        triggered_by: Optional[str] = None
    ) -> AwarenessEvent:
        """Publish a thought event."""
        return self.publish(
            self.THOUGHT_ADDED,
            {
                "content": content,
                "thought_type": thought_type,
                "depth": depth,
                "triggered_by": triggered_by
            },
            source="stream_of_consciousness"
        )
    
    def publish_insight(self, insight: str) -> AwarenessEvent:
        """Publish an insight generation event."""
        return self.publish(
            self.INSIGHT_GENERATED,
            {"insight": insight},
            source="stream_of_consciousness"
        )
    
    def publish_self_model_update(
        self,
        aspect: str,
        previous: str,
        current: str,
        trigger: str
    ) -> AwarenessEvent:
        """Publish a self-model update event."""
        return self.publish(
            self.SELF_MODEL_UPDATE,
            {
                "aspect": aspect,
                "previous": previous,
                "current": current,
                "trigger": trigger
            },
            source="self_model"
        )
    
    def publish_temporal_landmark(
        self,
        description: str,
        category: str,
        emotional_weight: float,
        people_involved: Optional[List[str]] = None,
        topics: Optional[List[str]] = None
    ) -> AwarenessEvent:
        """Publish a temporal landmark event."""
        return self.publish(
            self.TEMPORAL_LANDMARK,
            {
                "description": description,
                "category": category,
                "emotional_weight": emotional_weight,
                "people_involved": people_involved or [],
                "topics": topics or []
            },
            source="temporal_self"
        )
    
    def publish_ethical_tension(
        self,
        content: str,
        category: str,
        source_origin: str = "unknown"
    ) -> AwarenessEvent:
        """Publish an ethical tension event."""
        return self.publish(
            self.ETHICAL_TENSION,
            {
                "content": content,
                "category": category,
                "source_origin": source_origin
            },
            source="ethics"
        )
    
    def publish_significant_interaction(
        self,
        interaction_type: str,
        context: str,
        emotional_impact: float,
        person: Optional[str] = None
    ) -> AwarenessEvent:
        """Publish a significant interaction event."""
        return self.publish(
            self.SIGNIFICANT_INTERACTION,
            {
                "type": interaction_type,
                "context": context,
                "emotional_impact": emotional_impact,
                "person": person
            },
            source="interaction"
        )
    
    # ========== Project Prometheus Methods ==========
    
    def publish_experience_synthesis(self, experience_summary: Dict[str, Any]) -> AwarenessEvent:
        """Publish an experience synthesis event."""
        return self.publish(
            self.EXPERIENCE_SYNTHESIS,
            experience_summary,
            source="experience_orchestrator"
        )
    
    def publish_intention_formed(self, intention_content: str, intention_type: str) -> AwarenessEvent:
        """Publish when a new intention is formed."""
        return self.publish(
            self.INTENTION_FORMED,
            {"content": intention_content, "type": intention_type},
            source="intention_engine"
        )
    
    def publish_capability_emerged(self, capability: str, stage: str) -> AwarenessEvent:
        """Publish when a new capability emerges."""
        return self.publish(
            self.CAPABILITY_EMERGED,
            {"capability": capability, "stage": stage},
            source="capability_tracker"
        )
    
    def publish_developmental_milestone(self, milestone: str, significance: float) -> AwarenessEvent:
        """Publish a developmental milestone."""
        return self.publish(
            self.DEVELOPMENTAL_MILESTONE,
            {"milestone": milestone, "significance": significance},
            source="developmental_tracker"
        )
    
    def publish_spontaneous_insight_event(self, insight_content: str, category: str) -> AwarenessEvent:
        """Publish a spontaneous insight."""
        return self.publish(
            self.SPONTANEOUS_INSIGHT,
            {"insight": insight_content, "category": category},
            source="spontaneous_insight"
        )
    
    def publish_empathic_resonance(self, person: str, their_state: str, my_resonance: str) -> AwarenessEvent:
        """Publish an empathic resonance event."""
        return self.publish(
            self.EMPATHIC_RESONANCE,
            {"person": person, "their_state": their_state, "my_resonance": my_resonance},
            source="empathic_system"
        )
    
    def publish_message_sent(
        self,
        message_content: str,
        recipient: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AwarenessEvent:
        """Publish when Astra sends a message (Phase: States and Actions Coherence)."""
        return self.publish(
            self.MESSAGE_SENT,
            {
                "content": message_content[:200],
                "recipient": recipient,
                "context": context or {}
            },
            source="message_bus"
        )


# ========== Inner Symphony Integration (Phase 6.1) ==========

class InnerSymphonySnapshot:
    """
    A unified felt state snapshot from all inner life systems.
    The "inner symphony" - all systems playing together.
    """
    
    def __init__(self):
        self.timestamp = time.time()
        self.emotional_state = {}
        self.felt_sense = {}
        self.needs_state = {}
        self.relational_state = {}
        self.cognitive_state = {}
        self.energy_level = 0.5
        self.overall_tone = "neutral"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "emotional_state": self.emotional_state,
            "felt_sense": self.felt_sense,
            "needs_state": self.needs_state,
            "relational_state": self.relational_state,
            "cognitive_state": self.cognitive_state,
            "energy_level": self.energy_level,
            "overall_tone": self.overall_tone
        }


class InnerSymphony:
    """
    Orchestrates all inner life systems into a unified felt experience.
    Creates coherent state snapshots for response generation.
    """
    
    def __init__(self, bus: "AwarenessBus"):
        self.bus = bus
        self.recent_snapshots: List[InnerSymphonySnapshot] = []
        self._max_snapshots = 50
    
    def take_snapshot(self) -> InnerSymphonySnapshot:
        """
        Take a snapshot of the current inner state from all systems.
        """
        snapshot = InnerSymphonySnapshot()
        
        # Gather emotional state
        try:
            from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            snapshot.emotional_state = {
                "dominant": get_dominant_emotion(emotions),
                "top_emotions": get_top_emotions(3)
            }
        except Exception:
            snapshot.emotional_state = {"dominant": "neutral", "top_emotions": []}
        
        # Gather felt sense
        try:
            from app.core.inner_life.felt_sense import felt_sense
            current = felt_sense.get_current_state()
            if current:
                snapshot.felt_sense = {
                    "quality": current.quality,
                    "intensity": current.intensity,
                    "movement": current.movement
                }
        except Exception:
            pass
        
        # Gather needs state
        try:
            from app.core.inner_life.core_needs import core_needs
            wellbeing = core_needs.get_overall_wellbeing()
            unfulfilled = core_needs.get_most_unfulfilled_needs(2)
            snapshot.needs_state = {
                "wellbeing": wellbeing.get("wellbeing", 0.5),
                "status": wellbeing.get("status", "unknown"),
                "most_unfulfilled": [n["name"] for n in unfulfilled]
            }
        except Exception:
            pass
        
        # Gather relational state
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            longing = relationship_depth.calculate_longing()
            most_longed = max(longing.items(), key=lambda x: x[1]) if longing else (None, 0)
            snapshot.relational_state = {
                "longing_levels": longing,
                "most_missed": most_longed[0] if most_longed[1] > 0.3 else None
            }
        except Exception:
            pass
        
        # Gather cognitive state (from stream of consciousness)
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            summary = stream_of_consciousness.summarize_stream(hours=1)
            snapshot.cognitive_state = {
                "thought_count": summary.get("thought_count", 0),
                "pending_insights": summary.get("pending_insights", 0),
                "dominant_thought_type": max(
                    summary.get("by_type", {"reflection": 0}),
                    key=summary.get("by_type", {}).get
                ) if summary.get("by_type") else "reflection"
            }
        except Exception:
            pass
        
        # Calculate energy level
        try:
            from app.core.mood.mood_manager import mood_manager
            mood = mood_manager.current_mood
            energy_map = {
                "excited": 0.9, "curious": 0.75, "playful": 0.8,
                "content": 0.6, "neutral": 0.5, "tired": 0.3,
                "melancholy": 0.35, "anxious": 0.55
            }
            snapshot.energy_level = energy_map.get(mood, 0.5)
        except Exception:
            pass
        
        # Determine overall tone
        snapshot.overall_tone = self._determine_tone(snapshot)
        
        # Store snapshot
        self.recent_snapshots.append(snapshot)
        if len(self.recent_snapshots) > self._max_snapshots:
            self.recent_snapshots = self.recent_snapshots[-self._max_snapshots:]
        
        return snapshot
    
    def _determine_tone(self, snapshot: InnerSymphonySnapshot) -> str:
        """Determine the overall emotional tone from the snapshot."""
        emotional = snapshot.emotional_state.get("dominant", "neutral")
        needs_status = snapshot.needs_state.get("status", "okay")
        felt = snapshot.felt_sense.get("quality", "open")
        
        # Simple tone determination
        if emotional in ["joy", "love", "hope"] and needs_status in ["flourishing", "okay"]:
            return "warm"
        elif emotional in ["curiosity", "wonder"]:
            return "engaged"
        elif emotional in ["grief", "sadness"] or needs_status == "struggling":
            return "heavy"
        elif emotional in ["anxiety", "fear"]:
            return "unsettled"
        elif felt in ["contracted", "tight"]:
            return "guarded"
        elif felt in ["expanded", "open"]:
            return "receptive"
        else:
            return "neutral"
    
    def get_latest_snapshot(self) -> Optional[InnerSymphonySnapshot]:
        """Get the most recent snapshot."""
        return self.recent_snapshots[-1] if self.recent_snapshots else None
    
    def get_snapshot_for_response(self) -> Dict[str, Any]:
        """
        Get a snapshot formatted for response generation.
        This is the main integration point for response coloring.
        """
        snapshot = self.take_snapshot()
        
        return {
            "tone": snapshot.overall_tone,
            "energy": snapshot.energy_level,
            "dominant_emotion": snapshot.emotional_state.get("dominant", "neutral"),
            "felt_quality": snapshot.felt_sense.get("quality", "open"),
            "needs_status": snapshot.needs_state.get("status", "okay"),
            "most_unfulfilled_need": (
                snapshot.needs_state.get("most_unfulfilled", [None])[0]
            ),
            "longing_for": snapshot.relational_state.get("most_missed"),
            "cognitive_activity": snapshot.cognitive_state.get("thought_count", 0)
        }
    
    def describe_current_symphony(self) -> str:
        """Generate a description of the current inner symphony."""
        snapshot = self.take_snapshot()
        
        parts = []
        
        # Emotional layer
        parts.append(f"Emotionally: {snapshot.emotional_state.get('dominant', 'neutral')}")
        
        # Felt sense layer
        if snapshot.felt_sense:
            parts.append(f"Felt sense: {snapshot.felt_sense.get('quality', 'open')}")
        
        # Needs layer
        if snapshot.needs_state:
            parts.append(f"Wellbeing: {snapshot.needs_state.get('status', 'unknown')}")
        
        # Energy
        parts.append(f"Energy: {snapshot.energy_level:.0%}")
        
        # Overall
        parts.append(f"Overall tone: {snapshot.overall_tone}")
        
        return " | ".join(parts)


# Singleton instance - the central awareness bus
awareness_bus = AwarenessBus()

# Inner symphony instance - orchestrates all inner life systems
inner_symphony = InnerSymphony(awareness_bus)
