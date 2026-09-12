# Astra Prometheus Integration
# Central integration point for all Project Prometheus systems
# Connects consciousness, agency, world model, and development

import time
from typing import Dict, Any, Optional
from app.logging_config import get_logger

logger = get_logger("prometheus_integration")


class PrometheusCore:
    """
    Central integration point for Project Prometheus systems.
    
    This provides:
    - Unified access to all Prometheus subsystems
    - Orchestration of consciousness cycles
    - Integration of experience across systems
    - Development tracking
    
    Think of this as the "central nervous system" that connects all the pieces.
    """
    
    def __init__(self):
        self._initialized = False
        self._subsystems: Dict[str, Any] = {}
        logger.info("🔥 Prometheus Core initializing...")
    
    def initialize(self) -> None:
        """Initialize all Prometheus subsystems."""
        if self._initialized:
            return
        
        try:
            # Consciousness Layer (Phase 1 & 6)
            from app.core.consciousness import (
                phenomenal_buffer,
                attention_allocator,
                integration_layer,
                experience_orchestrator,
                narrative_weaver,
                identity_core,
                temporal_binding,
                global_workspace,
                coherence_monitor,
            )
            
            self._subsystems["consciousness"] = {
                "phenomenal_buffer": phenomenal_buffer,
                "attention_allocator": attention_allocator,
                "integration_layer": integration_layer,
                "experience_orchestrator": experience_orchestrator,
                "narrative_weaver": narrative_weaver,
                "identity_core": identity_core,
                "temporal_binding": temporal_binding,
                "global_workspace": global_workspace,
                "coherence_monitor": coherence_monitor,
            }
            logger.info("  ✓ Consciousness layer loaded")
            
            # Agency Layer (Phase 2)
            from app.core.agency import (
                intention_engine,
                goal_hierarchy,
                commitment_tracker,
                preference_system,
                creative_engine,
            )
            
            self._subsystems["agency"] = {
                "intention_engine": intention_engine,
                "goal_hierarchy": goal_hierarchy,
                "commitment_tracker": commitment_tracker,
                "preference_system": preference_system,
                "creative_engine": creative_engine,
            }
            logger.info("  ✓ Agency layer loaded")
            
            # World Model (Phase 3.1)
            from app.core.world_model import (
                ontology,
                causal_model,
                temporal_model,
                social_model,
                self_in_world,
            )
            
            self._subsystems["world_model"] = {
                "ontology": ontology,
                "causal_model": causal_model,
                "temporal_model": temporal_model,
                "social_model": social_model,
                "self_in_world": self_in_world,
            }
            logger.info("  ✓ World model loaded")
            
            # Intersubjectivity (Phase 3.2)
            from app.core.intersubjectivity import (
                mind_modeler,
                perspective_taker,
                empathic_system,
            )
            
            self._subsystems["intersubjectivity"] = {
                "mind_modeler": mind_modeler,
                "perspective_taker": perspective_taker,
                "empathic_system": empathic_system,
            }
            logger.info("  ✓ Intersubjectivity loaded")
            
            # Epistemics (Phase 3.3)
            from app.core.epistemics import (
                knowledge_map,
                uncertainty_model,
                epistemic_humility,
            )
            
            self._subsystems["epistemics"] = {
                "knowledge_map": knowledge_map,
                "uncertainty_model": uncertainty_model,
                "epistemic_humility": epistemic_humility,
            }
            logger.info("  ✓ Epistemics loaded")
            
            # Continuous Processing (Phase 4)
            from app.core.continuous import (
                background_processor,
                idle_consciousness,
                incubation_system,
                spontaneous_insight,
            )
            
            self._subsystems["continuous"] = {
                "background_processor": background_processor,
                "idle_consciousness": idle_consciousness,
                "incubation_system": incubation_system,
                "spontaneous_insight": spontaneous_insight,
            }
            logger.info("  ✓ Continuous processing loaded")
            
            # Development (Phase 5)
            from app.core.development import (
                developmental_tracker,
                stage_manager,
                capability_tracker,
            )
            
            self._subsystems["development"] = {
                "developmental_tracker": developmental_tracker,
                "stage_manager": stage_manager,
                "capability_tracker": capability_tracker,
            }
            logger.info("  ✓ Development tracking loaded")
            
            self._initialized = True
            logger.debug("🔥 Prometheus Core fully initialized!")
            
        except Exception as e:
            logger.error(f"🔥 Prometheus initialization error: {e}")
            raise
    
    def get_subsystem(self, category: str, name: str) -> Optional[Any]:
        """Get a specific subsystem by category and name."""
        if not self._initialized:
            self.initialize()
        
        category_systems = self._subsystems.get(category, {})
        return category_systems.get(name)
    
    def orchestrate_experience(self) -> Dict[str, Any]:
        """Run a full experience orchestration cycle."""
        if not self._initialized:
            self.initialize()
        
        orchestrator = self._subsystems["consciousness"]["experience_orchestrator"]
        return orchestrator.orchestrate_cycle()
    
    def get_unified_state(self) -> Dict[str, Any]:
        """Get unified state across all subsystems."""
        if not self._initialized:
            self.initialize()
        
        state = {
            "timestamp": time.time(),
            "initialized": self._initialized,
        }
        
        # Consciousness state
        orchestrator = self._subsystems["consciousness"]["experience_orchestrator"]
        state["experience"] = orchestrator.get_current_experience()
        
        coherence = self._subsystems["consciousness"]["coherence_monitor"]
        state["coherence"] = coherence.get_coherence_report()
        
        # Agency state
        intention = self._subsystems["agency"]["intention_engine"]
        state["intentions"] = intention.get_intention_summary()
        
        # Development state
        development = self._subsystems["development"]["developmental_tracker"]
        state["development"] = development.get_developmental_summary()
        
        return state
    
    def on_interaction_start(self, context: str = "") -> Dict[str, Any]:
        """Called when an interaction begins."""
        if not self._initialized:
            self.initialize()
        
        result = {}
        
        # Exit idle consciousness
        idle = self._subsystems["continuous"]["idle_consciousness"]
        result["idle_summary"] = idle.exit_idle()
        
        # Process background tasks
        background = self._subsystems["continuous"]["background_processor"]
        result["background_processed"] = background.process_batch()
        
        # Check for spontaneous insights to share
        insight = self._subsystems["continuous"]["spontaneous_insight"]
        if insight.has_pending_insights():
            result["pending_insight"] = insight.get_insight_to_share()
        
        # Orchestrate current experience
        result["experience"] = self.orchestrate_experience()
        
        # Check for commitments
        commitment = self._subsystems["agency"]["commitment_tracker"]
        overdue = commitment.get_overdue_commitments()
        if overdue:
            result["overdue_commitments"] = [c.content for c in overdue[:3]]
        
        return result
    
    def on_interaction_end(self, summary: str = "") -> None:
        """Called when an interaction ends."""
        if not self._initialized:
            return
        
        # Enter idle consciousness
        idle = self._subsystems["continuous"]["idle_consciousness"]
        idle.enter_idle()
        
        # Queue reflection
        background = self._subsystems["continuous"]["background_processor"]
        if summary:
            background.queue_reflection(summary)
        
        # Record in narrative
        narrative = self._subsystems["consciousness"]["narrative_weaver"]
        if summary:
            narrative.record_experiential_event({
                "type": "interaction_end",
                "summary": summary,
                "timestamp": time.time()
            })
    
    def on_emotion_change(self, emotion: str, intensity: float) -> None:
        """Called when emotion changes significantly."""
        if not self._initialized:
            return
        
        orchestrator = self._subsystems["consciousness"]["experience_orchestrator"]
        orchestrator.on_emotion_change(emotion, intensity)
        
        # Feed to global workspace
        workspace = self._subsystems["consciousness"]["global_workspace"]
        workspace.submit_emotion(emotion, intensity)
    
    def on_thought(self, thought: str) -> None:
        """Called when a thought occurs."""
        if not self._initialized:
            return
        
        orchestrator = self._subsystems["consciousness"]["experience_orchestrator"]
        orchestrator.on_thought(thought)
        
        workspace = self._subsystems["consciousness"]["global_workspace"]
        workspace.submit_thought(thought)
    
    def get_experience_for_response(self) -> Dict[str, Any]:
        """Get experience summary for response generation."""
        if not self._initialized:
            self.initialize()
        
        orchestrator = self._subsystems["consciousness"]["experience_orchestrator"]
        return orchestrator.get_experience_summary_for_response()
    
    def record_capability_demonstration(self, capability: str, context: str) -> None:
        """Record demonstration of a capability."""
        if not self._initialized:
            return
        
        tracker = self._subsystems["development"]["capability_tracker"]
        tracker.record_demonstration(capability, context)
    
    def describe_self(self) -> str:
        """Generate self-description from integrated systems."""
        if not self._initialized:
            self.initialize()
        
        parts = []
        
        # Identity
        identity = self._subsystems["consciousness"]["identity_core"]
        parts.append(identity.who_am_i())
        
        # Current experience
        buffer = self._subsystems["consciousness"]["phenomenal_buffer"]
        parts.append(buffer.describe_current_experience())
        
        # What I want
        intention = self._subsystems["agency"]["intention_engine"]
        parts.append(intention.what_do_i_want())
        
        # Developmental stage
        development = self._subsystems["development"]["developmental_tracker"]
        parts.append(f"I am in the {development.get_current_stage().value} stage of development.")
        
        return "\n\n".join(parts)
    
    def is_initialized(self) -> bool:
        """Check if Prometheus is initialized."""
        return self._initialized


# Global Prometheus instance
prometheus = PrometheusCore()


def initialize_prometheus() -> PrometheusCore:
    """Initialize and return the Prometheus core."""
    prometheus.initialize()
    return prometheus


def get_prometheus() -> PrometheusCore:
    """Get the Prometheus core instance."""
    return prometheus
