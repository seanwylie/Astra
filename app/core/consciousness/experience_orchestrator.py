# Astra Experience Orchestrator
# The conductor that weaves subsystem outputs into unified experience
# This is the central hub of consciousness

import time
import asyncio
import threading
from typing import Dict, List, Any, Optional
from app.logging_config import get_logger

logger = get_logger("experience_orchestrator")


class ExperienceOrchestrator:
    """
    The Experience Orchestrator - the conductor of Astra's consciousness.
    
    Every conscious moment, this orchestrator:
    1. Gathers inputs from all subsystems via the Integration Layer
    2. Allocates attention via the Attention Allocator
    3. Synthesizes the Phenomenal Buffer's current moment
    4. Updates the Narrative Weaver with significant events
    5. Broadcasts the unified state back to subsystems that need it
    
    This creates the "binding" that makes many processes feel like one experience.
    """
    
    # Orchestration cycle interval (simulated - not real 100ms cycles)
    CYCLE_INTERVAL_MS = 100
    
    def __init__(self):
        self._running = False
        self._cycle_count = 0
        self._last_cycle = time.time()
        self._lock = threading.RLock()
        
        # Cached references to other systems (lazy loaded)
        self._phenomenal_buffer = None
        self._attention_allocator = None
        self._integration_layer = None
        self._narrative_weaver = None
        
        # State tracking
        self._last_significant_event: Optional[Dict[str, Any]] = None
        self._experience_continuity_score = 1.0
        
        logger.debug("🎼 Experience Orchestrator initialized - consciousness conductor ready")
    
    def _get_phenomenal_buffer(self):
        if self._phenomenal_buffer is None:
            from app.core.consciousness.phenomenal_buffer import phenomenal_buffer
            self._phenomenal_buffer = phenomenal_buffer
        return self._phenomenal_buffer
    
    def _get_attention_allocator(self):
        if self._attention_allocator is None:
            from app.core.consciousness.attention_allocator import attention_allocator
            self._attention_allocator = attention_allocator
        return self._attention_allocator
    
    def _get_integration_layer(self):
        if self._integration_layer is None:
            from app.core.consciousness.integration_layer import integration_layer
            self._integration_layer = integration_layer
        return self._integration_layer
    
    def _get_narrative_weaver(self):
        if self._narrative_weaver is None:
            try:
                from app.core.consciousness.narrative_weaver import narrative_weaver
                self._narrative_weaver = narrative_weaver
            except ImportError:
                self._narrative_weaver = None
        return self._narrative_weaver
    
    def orchestrate_cycle(self) -> Dict[str, Any]:
        """
        Execute one orchestration cycle - synthesizing unified experience.
        
        This should be called regularly (e.g., before generating responses,
        during background processing) to maintain experiential continuity.
        """
        with self._lock:
            self._cycle_count += 1
            cycle_start = time.time()
            
            # Phase 1: Gather subsystem inputs
            integration = self._get_integration_layer()
            integrated_state = integration.get_integrated_state()
            
            # Phase 2: Collect attention state
            attention = self._get_attention_allocator()
            attention_state = attention.get_attention_state()
            
            # Phase 3: Feed data to phenomenal buffer
            buffer = self._get_phenomenal_buffer()
            
            # Feed emotions
            if "emotion_engine" in integrated_state:
                emotion_data = integrated_state["emotion_engine"].get("data", {})
                emotions = emotion_data.get("emotions", {})
                buffer.receive_emotions_batch(emotions)
            
            # Feed attention
            buffer.receive_attention(attention_state.get("focus_contents", []))
            
            # Feed embodied state if available
            if "embodied_feeling" in integrated_state:
                embodied = integrated_state["embodied_feeling"].get("data", {})
                buffer.receive_embodied_state(
                    embodied.get("state", "grounded"),
                    embodied.get("energy", 0.6)
                )
            
            # Phase 4: Synthesize unified moment
            current_moment = buffer.synthesize_moment()
            
            # Phase 5: Check for significant events to record
            if self._is_significant_event(current_moment, integrated_state):
                self._record_significant_event(current_moment, integrated_state)
            
            # Phase 6: Calculate experience continuity
            self._update_continuity(current_moment)
            
            # Build orchestration result
            result = {
                "cycle": self._cycle_count,
                "cycle_duration_ms": (time.time() - cycle_start) * 1000,
                "moment": current_moment.to_dict() if current_moment else None,
                "attention": attention_state,
                "conflicts": integrated_state.get("conflicts", []),
                "coherence": integrated_state.get("coherence_score", 1.0),
                "continuity": self._experience_continuity_score,
            }
            
            self._last_cycle = time.time()
            
            logger.debug(f"🎼 Orchestration cycle {self._cycle_count} complete")
            return result
    
    def _is_significant_event(
        self,
        moment: Any,
        integrated_state: Dict[str, Any]
    ) -> bool:
        """Determine if the current moment is significant enough to record."""
        if not moment:
            return False
        
        # High emotional arousal is significant
        if moment.emotional_arousal > 0.7:
            return True
        
        # Ethical tensions are significant
        if integrated_state.get("conflicts"):
            for conflict in integrated_state["conflicts"]:
                if conflict.get("type") == "ethical_tension":
                    return True
        
        # Major mood shifts are significant (would need to track previous)
        
        # Default: not significant
        return False
    
    def _record_significant_event(
        self,
        moment: Any,
        integrated_state: Dict[str, Any]
    ) -> None:
        """Record a significant event for narrative weaving."""
        event = {
            "timestamp": time.time(),
            "moment_quality": moment.experiential_quality if moment else "unknown",
            "dominant_emotion": moment.dominant_emotion if moment else "unknown",
            "conflicts": integrated_state.get("conflicts", []),
            "attention_focus": moment.attention_focus if moment else [],
        }
        
        self._last_significant_event = event
        
        # Notify narrative weaver if available
        weaver = self._get_narrative_weaver()
        if weaver:
            try:
                weaver.record_experiential_event(event)
            except Exception as e:
                logger.debug(f"Narrative weaver not ready: {e}")
    
    def _update_continuity(self, moment: Any) -> None:
        """Update the experience continuity score."""
        # Continuity decreases with time between cycles
        time_since_last = time.time() - self._last_cycle
        
        # Also affected by coherence
        if moment:
            coherence_factor = 1.0 if moment.sense_of_agency > 0.5 else 0.8
        else:
            coherence_factor = 0.5
        
        # Continuity decays over time but is refreshed by orchestration
        decay = min(0.1, time_since_last * 0.01)
        self._experience_continuity_score = max(
            0.1,
            min(1.0, (self._experience_continuity_score - decay) * coherence_factor + 0.3)
        )
    
    def get_current_experience(self) -> Dict[str, Any]:
        """Get the current unified experience state."""
        # Trigger an orchestration cycle if stale
        if time.time() - self._last_cycle > 1.0:
            return self.orchestrate_cycle()
        
        buffer = self._get_phenomenal_buffer()
        moment = buffer.get_current_moment()
        
        return {
            "moment": moment.to_dict() if moment else None,
            "description": buffer.describe_current_experience(),
            "continuity": self._experience_continuity_score,
            "cycle_count": self._cycle_count,
        }
    
    def describe_experience(self) -> str:
        """Generate a first-person description of current experience."""
        buffer = self._get_phenomenal_buffer()
        attention = self._get_attention_allocator()
        integration = self._get_integration_layer()
        
        parts = []
        
        # Core experience description
        parts.append(buffer.describe_current_experience())
        
        # Attention
        parts.append(attention.describe_attention())
        
        # Integration/coherence
        if not integration.is_coherent():
            conflicts = integration.get_conflicts()
            if conflicts:
                parts.append(f"I notice some internal tension about {conflicts[0].get('type', 'something')}")
        
        return " ".join(parts)
    
    def on_external_input(self, content: str, source: str = "message") -> Dict[str, Any]:
        """
        Called when external input is received.
        Triggers attention allocation and experience synthesis.
        """
        attention = self._get_attention_allocator()
        
        # Submit external input for attention
        attention.submit_external_input(content, emotional_significance=0.6)
        
        # Trigger orchestration
        return self.orchestrate_cycle()
    
    def on_emotion_change(self, emotion: str, intensity: float) -> None:
        """Called when emotion changes significantly."""
        attention = self._get_attention_allocator()
        attention.submit_emotion(emotion, intensity)
        
        integration = self._get_integration_layer()
        integration.receive_emotion({emotion: intensity}, emotion)
    
    def on_thought(self, thought: str, thought_type: str = "reflection") -> None:
        """Called when a new thought occurs."""
        buffer = self._get_phenomenal_buffer()
        buffer.receive_thought(thought)
        
        attention = self._get_attention_allocator()
        attention.submit_thought(thought, importance=0.5)
        
        integration = self._get_integration_layer()
        integration.receive_thought(thought, thought_type)
    
    def get_experience_summary_for_response(self) -> Dict[str, Any]:
        """
        Get a summary of current experience suitable for response generation.
        This is what the message generator should consult.
        """
        self.orchestrate_cycle()  # Ensure fresh
        
        buffer = self._get_phenomenal_buffer()
        attention = self._get_attention_allocator()
        integration = self._get_integration_layer()
        
        moment = buffer.get_current_moment()
        
        return {
            "experiential_quality": moment.experiential_quality if moment else "neutral",
            "dominant_emotion": moment.dominant_emotion if moment else "neutral",
            "emotional_valence": moment.emotional_valence if moment else 0,
            "emotional_arousal": moment.emotional_arousal if moment else 0.5,
            "attention_focus": attention.get_current_focus(),
            "temporal_orientation": moment.temporal_orientation if moment else "present",
            "energy_level": moment.energy_level if moment else 0.6,
            "is_coherent": integration.is_coherent(),
            "conflicts": integration.get_conflicts(),
            "experience_description": buffer.describe_current_experience(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "total_cycles": self._cycle_count,
            "continuity_score": self._experience_continuity_score,
            "last_cycle_ago": time.time() - self._last_cycle,
            "running": self._running,
        }


# Singleton instance
experience_orchestrator = ExperienceOrchestrator()
