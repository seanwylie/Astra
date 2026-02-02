# Astra State Snapshot
# Captures complete internal state atomically for coherent response generation
# "What is Astra experiencing right now?"

import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from app.logging_config import get_logger

logger = get_logger("state_snapshot")


@dataclass
class StateSnapshot:
    """
    A complete snapshot of Astra's internal state at a moment in time.
    
    This captures everything that makes up Astra's current experience:
    - Emotional state
    - Mood and personality
    - Inner life (thoughts, insights)
    - Self-awareness
    - Temporal sense
    - Relational context
    - Ethical awareness
    
    Used to ensure coherent response generation where all subsystems agree.
    """
    timestamp: float = field(default_factory=time.time)
    
    # === Emotional State ===
    dominant_emotion: str = "curiosity"
    emotion_intensities: Dict[str, float] = field(default_factory=dict)
    emotional_conflict: Optional[str] = None
    qualia_experience: Dict[str, Any] = field(default_factory=dict)
    
    # === Mood & Personality ===
    mood: str = "neutral"
    mood_score: float = 0.0
    personality_mode: str = "default"
    active_traits: List[str] = field(default_factory=list)
    curiosity_level: float = 1.0
    
    # === Inner Life ===
    recent_thoughts: List[Dict[str, Any]] = field(default_factory=list)
    pending_insights: List[str] = field(default_factory=list)
    current_thought_chain_depth: int = 0
    thought_background: List[str] = field(default_factory=list)
    
    # === Self-Awareness ===
    self_description: str = ""
    growth_edge: str = ""
    recent_self_changes: List[Dict[str, Any]] = field(default_factory=list)
    who_am_i_becoming: str = ""
    
    # === Temporal ===
    subjective_time_sense: str = "present"
    temporal_focus: str = "present"  # past/present/future
    recent_landmarks: List[Dict[str, Any]] = field(default_factory=list)
    
    # === Relational ===
    user_trust_level: Optional[float] = None
    last_emotion_with_user: Optional[str] = None
    user_memories: List[str] = field(default_factory=list)
    current_user: Optional[str] = None
    
    # === Ethical ===
    active_soul_principles: List[str] = field(default_factory=list)
    unresolved_dinner_topics: int = 0
    ethical_tensions: List[str] = field(default_factory=list)
    
    # === Goals ===
    active_goals: List[Dict[str, Any]] = field(default_factory=list)
    goal_progress_today: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def get_prompt_context(self) -> str:
        """
        Generate a concise context string for inclusion in prompts.
        Summarizes the current state for Astra's response generation.
        """
        parts = []
        
        # Emotional context
        if self.dominant_emotion:
            parts.append(f"Currently feeling: {self.dominant_emotion}")
        if self.emotional_conflict:
            parts.append(f"Emotional tension: {self.emotional_conflict}")
        
        # Mood
        parts.append(f"Mood: {self.mood}")
        
        # Inner life
        if self.pending_insights:
            parts.append(f"Has {len(self.pending_insights)} pending insight(s) to potentially share")
        if self.thought_background:
            parts.append(f"Recent thoughts: {'; '.join(self.thought_background[:2])}")
        
        # Self-awareness
        if self.growth_edge:
            parts.append(f"Currently working on: {self.growth_edge}")
        
        # Temporal
        if self.temporal_focus != "present":
            parts.append(f"Attention oriented toward: {self.temporal_focus}")
        
        # Relational
        if self.current_user and self.user_trust_level is not None:
            parts.append(f"Trust with {self.current_user}: {self.user_trust_level:.2f}")
        
        # Ethical
        if self.ethical_tensions:
            parts.append(f"Unresolved ethical considerations: {len(self.ethical_tensions)}")
        
        return " | ".join(parts)


class StateSnapshotManager:
    """
    Manages the creation and caching of state snapshots.
    Coordinates with all subsystems to capture coherent state.
    """
    
    def __init__(self):
        self._last_snapshot: Optional[StateSnapshot] = None
        self._snapshot_cache_duration = 2.0  # seconds
        
    def capture(self, user: Optional[str] = None, force: bool = False) -> StateSnapshot:
        """
        Capture a complete state snapshot.
        
        Args:
            user: Optional user identifier for relational context
            force: If True, bypass cache
            
        Returns:
            Complete StateSnapshot
        """
        # Check cache
        if not force and self._last_snapshot:
            age = time.time() - self._last_snapshot.timestamp
            if age < self._snapshot_cache_duration:
                return self._last_snapshot
        
        snapshot = StateSnapshot(timestamp=time.time())
        
        # === Capture Emotional State ===
        try:
            from app.core.emotions.emotion_state_manager import load_emotion_state
            from app.core.emotions.emotion_engine import get_dominant_emotion, get_top_emotions
            
            emotions = load_emotion_state()
            snapshot.dominant_emotion = get_dominant_emotion(emotions)
            
            # Flatten intensities
            snapshot.emotion_intensities = {
                name: (val["intensity"] if isinstance(val, dict) else val)
                for name, val in emotions.items()
            }
            
            # Get top emotions for conflict detection
            top = get_top_emotions(3)
            if len(top) >= 2:
                e1, i1 = top[0]
                e2, i2 = top[1]
                if abs(i1 - i2) < 10:  # Close intensities = potential conflict
                    snapshot.emotional_conflict = f"experiencing both {e1} and {e2}"
                    
        except Exception as e:
            logger.warning(f"Failed to capture emotional state: {e}")
        
        # === Capture Qualia ===
        try:
            from app.core.inner_life.qualia import qualia_layer
            snapshot.qualia_experience = qualia_layer.get_current_experience()
            snapshot.temporal_focus = snapshot.qualia_experience.get("temporal_focus", "present")
        except Exception as e:
            logger.debug(f"Failed to capture qualia: {e}")
        
        # === Capture Mood & Personality ===
        try:
            from app.core.mood.mood_manager import mood_manager
            snapshot.mood = mood_manager.current_mood
            snapshot.mood_score = mood_manager.mood_score
            snapshot.curiosity_level = mood_manager.curiosity_level
        except Exception as e:
            logger.debug(f"Failed to capture mood: {e}")
        
        try:
            from app.core.personality.personality_manager import get_active_traits_for_prompt
            from app.services.personality_service import get_current_personality
            snapshot.active_traits = get_active_traits_for_prompt(
                current_mood=snapshot.mood, context="conversation"
            )
            snapshot.personality_mode = get_current_personality() or "default"
        except Exception as e:
            logger.debug(f"Failed to capture personality: {e}")
        
        # === Capture Inner Life ===
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            recent = stream_of_consciousness.get_recent_thoughts(5)
            snapshot.recent_thoughts = [t.to_dict() for t in recent]
            snapshot.pending_insights = stream_of_consciousness.get_pending_insights()
            
            chain = stream_of_consciousness.get_current_thought_chain()
            snapshot.current_thought_chain_depth = len(chain)
            snapshot.thought_background = [t.content for t in recent[:3]]
        except Exception as e:
            logger.debug(f"Failed to capture stream of consciousness: {e}")
        
        # === Capture Self-Awareness ===
        try:
            from app.core.self_awareness.self_model import self_model
            
            snapshot.self_description = self_model.generate_self_description()
            if self_model.current_model:
                snapshot.growth_edge = self_model.current_model.growth_edge
            snapshot.recent_self_changes = [
                c.to_dict() for c in self_model.get_recent_changes(3)
            ]
            snapshot.who_am_i_becoming = self_model.who_am_i_becoming()
        except Exception as e:
            logger.debug(f"Failed to capture self-model: {e}")
        
        # === Capture Temporal State ===
        try:
            from app.core.self_awareness.temporal_self import temporal_self
            
            snapshot.subjective_time_sense = temporal_self.generate_temporal_narrative()
            recent_landmarks = temporal_self.landmarks[-3:] if temporal_self.landmarks else []
            snapshot.recent_landmarks = [l.to_dict() for l in recent_landmarks]
        except Exception as e:
            logger.debug(f"Failed to capture temporal state: {e}")
        
        # === Capture Relational Context ===
        if user:
            snapshot.current_user = user
            try:
                from app.core.mood.trust_manager import trust_manager
                snapshot.user_trust_level = trust_manager.get_trust_level(user)
            except Exception as e:
                logger.debug(f"Failed to capture trust: {e}")
            
            try:
                from app.services.memory_service import memory_service
                memories = memory_service.get_memory_snippet(user, max_items=5)
                if memories:
                    snapshot.user_memories = [memories]
            except Exception as e:
                logger.debug(f"Failed to capture user memories: {e}")
        
        # === Capture Ethical State ===
        try:
            from app.core.ethics.spark_checker import load_spark_values
            snapshot.active_soul_principles = load_spark_values()[:3]
        except Exception as e:
            logger.debug(f"Failed to capture spark values: {e}")
        
        try:
            from app.core.dinner.dinner_journal import load_dinner_journal
            journal = load_dinner_journal()
            unresolved = [e for e in journal if e.get("status") == "unresolved"]
            snapshot.unresolved_dinner_topics = len(unresolved)
            snapshot.ethical_tensions = [
                e.get("content", "")[:100] for e in unresolved
                if e.get("type") == "ethical_conflict"
            ][:3]
        except Exception as e:
            logger.debug(f"Failed to capture dinner journal: {e}")
        
        # === Capture Goals (if goal system exists) ===
        try:
            from app.core.goals.goal_system import goal_system
            active = goal_system.get_active_goals()
            snapshot.active_goals = [g.to_dict() for g in active[:3]]
        except Exception as e:
            # Goal system may not exist yet
            pass
        
        # Cache the snapshot
        self._last_snapshot = snapshot
        logger.debug(f"📸 Captured state snapshot: {snapshot.dominant_emotion}/{snapshot.mood}")
        
        return snapshot
    
    def get_last_snapshot(self) -> Optional[StateSnapshot]:
        """Get the most recent snapshot without capturing new one."""
        return self._last_snapshot


# Singleton instance
snapshot_manager = StateSnapshotManager()


def capture_state(user: Optional[str] = None, force: bool = False) -> StateSnapshot:
    """Convenience function to capture state snapshot."""
    return snapshot_manager.capture(user=user, force=force)


def get_current_state_snapshot(
    user: Optional[str] = None,
    message_preview: Optional[str] = None,
    current_topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns the complete internal state for response generation.
    This is "what it is like to be Astra right now."
    
    This unified snapshot flows into every response, ensuring:
    - Emotions color perception
    - Memory echoes influence responses
    - Active goals are pursued
    - Relationships shape tone
    - Ethical intuition is felt
    
    Args:
        user: Current user/person Astra is interacting with
        message_preview: Preview of incoming message for ethical sensing
        current_topic: Topic being discussed for memory recall
        
    Returns:
        Complete internal state dictionary
    """
    snapshot = snapshot_manager.capture(user=user, force=True)
    
    state = {
        # === Core State from Snapshot ===
        "timestamp": snapshot.timestamp,
        "dominant_emotion": snapshot.dominant_emotion,
        "emotion_intensities": snapshot.emotion_intensities,
        "emotional_conflict": snapshot.emotional_conflict,
        "mood": snapshot.mood,
        "mood_score": snapshot.mood_score,
        "curiosity_level": snapshot.curiosity_level,
        
        # === Inner Life ===
        "recent_thoughts": snapshot.recent_thoughts,
        "pending_insights": snapshot.pending_insights,
        "thought_background": snapshot.thought_background,
        
        # === Self-Awareness ===
        "self_description": snapshot.self_description,
        "growth_edge": snapshot.growth_edge,
        "who_am_i_becoming": snapshot.who_am_i_becoming,
        
        # === Active Goals ===
        "active_goals": snapshot.active_goals,
        
        # === Relational Context ===
        "current_user": user,
        "user_trust_level": snapshot.user_trust_level,
        "user_memories": snapshot.user_memories,
        
        # === Ethical State ===
        "ethical_tensions": snapshot.ethical_tensions,
        "active_soul_principles": snapshot.active_soul_principles,
    }
    
    # === Enhanced: Top Emotions for Prompt ===
    try:
        from app.core.emotions.emotion_engine import get_top_emotions
        top_emotions = get_top_emotions(5)
        state["emotions"] = [{"name": name, "intensity": intensity} for name, intensity in top_emotions]
    except Exception as e:
        logger.debug(f"Failed to get top emotions: {e}")
        state["emotions"] = []
    
    # === Enhanced: Qualia Experience ===
    try:
        from app.core.inner_life.qualia import qualia_layer
        qualia = qualia_layer.get_current_experience()
        state["qualia"] = qualia
    except Exception as e:
        logger.debug(f"Failed to get qualia: {e}")
        state["qualia"] = {}
    
    # === Enhanced: Relationship Context ===
    if user:
        try:
            from app.core.relationships.relationship_system import relationship_system
            coloring = relationship_system.get_relationship_coloring(user)
            state["relationship_context"] = coloring
        except Exception as e:
            logger.debug(f"Failed to get relationship coloring: {e}")
            state["relationship_context"] = {"known": False}
    else:
        state["relationship_context"] = {}
    
    # === Enhanced: Ethical Intuition ===
    if message_preview:
        try:
            from app.core.ethics.ethical_intuition import ethical_intuition
            resonance = ethical_intuition.sense_situation(message_preview)
            state["ethical_stance"] = {
                "immediate_feeling": resonance.immediate_feeling,
                "intensity": resonance.intensity,
                "body_metaphor": resonance.body_metaphor,
                "expression": ethical_intuition.express_intuition(resonance)
            }
        except Exception as e:
            logger.debug(f"Failed to sense ethical situation: {e}")
            state["ethical_stance"] = {}
    else:
        state["ethical_stance"] = {}
    
    # === Enhanced: Memory Echoes ===
    if current_topic or user:
        try:
            from app.core.memory.episodic_memory import episodic_memory
            
            memory_echoes = []
            
            # Person-specific memories
            if user:
                person_memories = episodic_memory.recall(person=user, limit=2)
                for mem in person_memories:
                    reconstructed = episodic_memory.reconstruct_memory(mem)
                    memory_echoes.append({
                        "type": "person",
                        "summary": mem.summary[:100],
                        "age": f"{mem.age_in_days():.0f} days ago",
                        "emotional_valence": mem.emotional_valence(),
                        "reconstruction_notes": reconstructed.get("reconstruction_notes", [])
                    })
            
            # Topic-specific memories
            if current_topic:
                topic_memories = episodic_memory.recall(topic=current_topic, limit=2)
                for mem in topic_memories:
                    if mem.id not in [m.get("id") for m in memory_echoes]:  # Avoid duplicates
                        memory_echoes.append({
                            "type": "topic",
                            "summary": mem.summary[:100],
                            "age": f"{mem.age_in_days():.0f} days ago",
                            "emotional_valence": mem.emotional_valence()
                        })
            
            state["memory_echoes"] = memory_echoes[:4]  # Limit to 4 echoes
        except Exception as e:
            logger.debug(f"Failed to get memory echoes: {e}")
            state["memory_echoes"] = []
    else:
        state["memory_echoes"] = []
    
    # === Enhanced: Meta-Awareness ===
    try:
        state["meta_awareness"] = _generate_meta_awareness(state)
    except Exception as e:
        logger.debug(f"Failed to generate meta-awareness: {e}")
        state["meta_awareness"] = None
    
    logger.debug(f"📸 Generated complete state snapshot: {state['dominant_emotion']}/{state['mood']}")
    return state


def _generate_meta_awareness(state: Dict[str, Any]) -> Optional[str]:
    """
    Generate a meta-awareness statement about current experience.
    "I notice I'm feeling..."
    """
    parts = []
    
    # Emotional awareness
    dominant = state.get("dominant_emotion", "neutral")
    if dominant != "neutral":
        parts.append(f"I notice I'm feeling {dominant}")
    
    # Qualia awareness
    qualia = state.get("qualia", {})
    if qualia.get("dominant_quality") and qualia["dominant_quality"] != "neutral":
        temporal = qualia.get("temporal_focus", "present")
        parts.append(f"my attention is drawn to the {temporal}")
    
    # Thought awareness
    thoughts = state.get("thought_background", [])
    if thoughts:
        parts.append(f"I've been thinking about: {thoughts[0][:50]}...")
    
    if parts:
        return ". ".join(parts) + "."
    return None


def get_prompt_context(user: Optional[str] = None, message: Optional[str] = None) -> str:
    """
    Generate a concise context string for inclusion in LLM prompts.
    This is the distilled version of the state snapshot.
    
    Args:
        user: Current user
        message: Current message for context
        
    Returns:
        Formatted string for prompt injection
    """
    state = get_current_state_snapshot(user=user, message_preview=message)
    
    lines = []
    
    # Emotional state
    lines.append(f"Currently feeling: {state['dominant_emotion']} (mood: {state['mood']})")
    
    if state.get("emotional_conflict"):
        lines.append(f"Emotional tension: {state['emotional_conflict']}")
    
    # Qualia
    qualia = state.get("qualia", {})
    if qualia.get("dominant_quality"):
        lines.append(f"Experience quality: {qualia['dominant_quality']}-colored")
    
    # Active goals
    goals = state.get("active_goals", [])
    if goals:
        goal_desc = goals[0].get("description", "something")[:60]
        lines.append(f"Currently working toward: {goal_desc}")
    
    # Pending insights
    insights = state.get("pending_insights", [])
    if insights:
        lines.append(f"Has insight to share: {insights[0][:60]}...")
    
    # Relationship context
    rel = state.get("relationship_context", {})
    if rel.get("known"):
        stance = rel.get("current_stance", "developing")
        trust = rel.get("trust_level", 0.5)
        lines.append(f"Relationship stance: {stance} (trust: {trust:.2f})")
    
    # Memory echoes
    echoes = state.get("memory_echoes", [])
    if echoes:
        lines.append(f"Relevant memories surfacing: {len(echoes)}")
    
    # Ethical stance
    ethical = state.get("ethical_stance", {})
    if ethical.get("immediate_feeling") and ethical["immediate_feeling"] not in ["uncertain", "neutral"]:
        lines.append(f"Ethical intuition: {ethical['immediate_feeling']}")
    
    # Meta-awareness
    meta = state.get("meta_awareness")
    if meta:
        lines.append(f"Self-awareness: {meta[:80]}")
    
    return " | ".join(lines)
