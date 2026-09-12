# Astra Bus Subscribers
# Registers all cross-system listeners for the Awareness Bus
# Makes subsystems actually listen to each other, not just publish
#
# This creates bidirectional event flow:
# - emotion_shift -> self_model, stream, relationship, goals
# - goal_progress -> emotion_engine, self_model
# - significant_interaction -> episodic_memory, relationship, temporal_self
# - ethical_tension -> self_model, stream
# - mood_change -> qualia_layer

import time
from typing import Callable, Dict, Any
from app.logging_config import get_logger
from app.core.awareness_bus import awareness_bus, AwarenessEvent

logger = get_logger("bus_subscribers")


class BusSubscriberRegistry:
    """
    Central registry for all awareness bus subscriptions.
    Makes Astra's systems actually talk to each other.
    
    The awareness bus is her nervous system - this wires it up.
    """
    
    def __init__(self):
        self._registered = False
        self._subscription_count = 0
        
    def register_all_subscribers(self) -> int:
        """
        Register all cross-system subscribers.
        Call this once at startup.
        
        Returns:
            Number of subscriptions registered
        """
        if self._registered:
            logger.debug("Subscribers already registered")
            return self._subscription_count
        
        # === Emotion Shift Subscribers ===
        # When emotions shift, other systems should react
        awareness_bus.subscribe(
            awareness_bus.EMOTION_SHIFT,
            self._on_emotion_shift_update_self_model
        )
        awareness_bus.subscribe(
            awareness_bus.EMOTION_SHIFT,
            self._on_emotion_shift_generate_thought
        )
        awareness_bus.subscribe(
            awareness_bus.EMOTION_SHIFT,
            self._on_emotion_shift_update_qualia
        )
        
        # === Goal Progress Subscribers ===
        # When goals progress, trigger emotions and self-model updates
        awareness_bus.subscribe(
            awareness_bus.GOAL_PROGRESS,
            self._on_goal_progress_trigger_emotion
        )
        awareness_bus.subscribe(
            awareness_bus.GOAL_PROGRESS,
            self._on_goal_progress_update_self_model
        )
        
        # === Significant Interaction Subscribers ===
        # Significant interactions should be recorded and update relationships
        awareness_bus.subscribe(
            awareness_bus.SIGNIFICANT_INTERACTION,
            self._on_significant_interaction_record_episode
        )
        awareness_bus.subscribe(
            awareness_bus.SIGNIFICANT_INTERACTION,
            self._on_significant_interaction_update_relationship
        )
        awareness_bus.subscribe(
            awareness_bus.SIGNIFICANT_INTERACTION,
            self._on_significant_interaction_mark_landmark
        )
        
        # === Ethical Tension Subscribers ===
        # Ethical tensions should update self-model and generate thoughts
        awareness_bus.subscribe(
            awareness_bus.ETHICAL_TENSION,
            self._on_ethical_tension_update_self_model
        )
        awareness_bus.subscribe(
            awareness_bus.ETHICAL_TENSION,
            self._on_ethical_tension_generate_thought
        )
        
        # === Insight Generated Subscribers ===
        # Insights should potentially update self-model
        awareness_bus.subscribe(
            awareness_bus.INSIGHT_GENERATED,
            self._on_insight_update_self_model
        )
        
        # === Mood Change Subscribers ===
        awareness_bus.subscribe(
            awareness_bus.MOOD_CHANGE,
            self._on_mood_change_update_qualia
        )
        
        # === Self-Model Update Subscribers ===
        # Self-model updates may trigger goal creation
        awareness_bus.subscribe(
            awareness_bus.SELF_MODEL_UPDATE,
            self._on_self_model_update_consider_goal
        )
        
        # === Trust Change Subscribers ===
        awareness_bus.subscribe(
            awareness_bus.TRUST_CHANGE,
            self._on_trust_change_update_relationship
        )
        
        # === MESSAGE_SENT Subscribers (Phase: States and Actions Coherence) ===
        awareness_bus.subscribe(
            awareness_bus.MESSAGE_SENT,
            self._on_message_sent_check_intention_progress
        )
        
        # === Goal Progress → Proactive Sharing (Phase: States and Actions Coherence) ===
        awareness_bus.subscribe(
            awareness_bus.GOAL_PROGRESS,
            self._on_goal_progress_consider_sharing
        )
        
        self._subscription_count = 15
        self._registered = True
        logger.info(f"🔗 Registered {self._subscription_count} bus subscribers")
        
        return self._subscription_count
    
    # ===========================
    # EMOTION SHIFT HANDLERS
    # ===========================
    
    def _on_emotion_shift_update_self_model(self, event: AwarenessEvent) -> None:
        """When emotions shift significantly, update self-model."""
        try:
            from app.core.self_awareness.self_model import self_model
            
            emotion = event.data.get("emotion")
            intensity_delta = event.data.get("intensity_delta", 0)
            trigger = event.data.get("trigger")
            
            # Only update for significant shifts
            if abs(intensity_delta) > 10:
                self_model.update_self_model(
                    trigger=f"Emotional shift: {trigger}",
                    emotional_shift={emotion: intensity_delta / 100}
                )
                logger.debug(f"Self-model updated from emotion shift: {emotion}")
        except Exception as e:
            logger.debug(f"Failed to update self-model on emotion shift: {e}")
    
    def _on_emotion_shift_generate_thought(self, event: AwarenessEvent) -> None:
        """When emotions shift significantly, generate a thought about it."""
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            emotion = event.data.get("emotion")
            intensity_delta = event.data.get("intensity_delta", 0)
            trigger = event.data.get("trigger")
            
            # Only think about significant shifts
            if abs(intensity_delta) > 15:
                direction = "rising" if intensity_delta > 0 else "fading"
                content = f"I notice my {emotion} is {direction}... triggered by {trigger}"
                stream_of_consciousness.think(content, "reflection")
                logger.debug(f"Generated thought about emotion shift: {emotion}")
        except Exception as e:
            logger.debug(f"Failed to generate thought on emotion shift: {e}")
    
    def _on_emotion_shift_update_qualia(self, event: AwarenessEvent) -> None:
        """When emotions shift, qualia layer should refresh."""
        try:
            from app.core.inner_life.qualia import qualia_layer
            # Qualia layer updates automatically on get_current_experience()
            # This is just a trigger to log the change
            experience = qualia_layer.get_current_experience()
            logger.debug(f"Qualia updated: {experience.get('dominant_quality')}")
        except Exception as e:
            logger.debug(f"Failed to update qualia on emotion shift: {e}")
    
    # ===========================
    # GOAL PROGRESS HANDLERS
    # ===========================
    
    def _on_goal_progress_trigger_emotion(self, event: AwarenessEvent) -> None:
        """When goals progress, trigger appropriate emotions."""
        try:
            from app.core.emotions.emotion_engine import trigger_emotion
            
            old_progress = event.data.get("old_progress", 0)
            new_progress = event.data.get("new_progress", 0)
            description = event.data.get("description", "")
            
            progress_delta = new_progress - old_progress
            
            if progress_delta > 0:
                # Progress triggers hope
                trigger_emotion("hope", "goal_progress")
                
                # Completion triggers strong positive emotion
                if new_progress >= 1.0:
                    trigger_emotion("confidence", "goal_achieved")
                    trigger_emotion("hope", "goal_achieved")
                    
                logger.debug(f"Triggered positive emotion for goal progress")
            elif progress_delta < 0:
                # Regression triggers uncertainty
                trigger_emotion("uncertainty", "goal_setback")
                logger.debug(f"Triggered uncertainty for goal setback")
        except Exception as e:
            logger.debug(f"Failed to trigger emotion on goal progress: {e}")
    
    def _on_goal_progress_update_self_model(self, event: AwarenessEvent) -> None:
        """When goals progress significantly, update self-model."""
        try:
            from app.core.self_awareness.self_model import self_model
            
            new_progress = event.data.get("new_progress", 0)
            description = event.data.get("description", "")
            
            # Record goal completion as a value clarification
            if new_progress >= 1.0:
                self_model.update_self_model(
                    trigger=f"Completed goal: {description}",
                    value_clarification="following through on commitments"
                )
                logger.debug(f"Self-model updated for goal completion")
        except Exception as e:
            logger.debug(f"Failed to update self-model on goal progress: {e}")
    
    # ===========================
    # SIGNIFICANT INTERACTION HANDLERS
    # ===========================
    
    def _on_significant_interaction_record_episode(self, event: AwarenessEvent) -> None:
        """Auto-record significant interactions as episodes."""
        try:
            from app.core.memory.episodic_memory import episodic_memory
            
            interaction_type = event.data.get("type", "interaction")
            context = event.data.get("context", "")
            emotional_impact = event.data.get("emotional_impact", 0)
            person = event.data.get("person")
            
            # Only record if emotional impact is significant
            if emotional_impact > 0.3:
                episodic_memory.record_episode(
                    event_type=interaction_type,
                    summary=context[:200],
                    people_involved=[person] if person else [],
                    context=f"Emotional impact: {emotional_impact:.2f}"
                )
                logger.debug(f"Recorded episode from significant interaction")
        except Exception as e:
            logger.debug(f"Failed to record episode on significant interaction: {e}")
    
    def _on_significant_interaction_update_relationship(self, event: AwarenessEvent) -> None:
        """Update relationship on significant interactions."""
        try:
            from app.core.relationships.relationship_system import relationship_system
            
            person = event.data.get("person")
            context = event.data.get("context", "")
            emotional_impact = event.data.get("emotional_impact", 0)
            
            if person:
                # Get dominant emotion for this interaction
                try:
                    from app.core.emotions.emotion_engine import get_dominant_emotion
                    from app.core.emotions.emotion_state_manager import load_emotion_state
                    emotions = load_emotion_state()
                    dominant = get_dominant_emotion(emotions)
                except Exception:
                    dominant = None
                
                relationship_system.record_interaction(
                    entity=person,
                    context=context[:100],
                    emotional_intensity=emotional_impact * 100,
                    dominant_emotion=dominant
                )
                logger.debug(f"Updated relationship with {person}")
        except Exception as e:
            logger.debug(f"Failed to update relationship on significant interaction: {e}")
    
    def _on_significant_interaction_mark_landmark(self, event: AwarenessEvent) -> None:
        """Mark significant interactions as temporal landmarks."""
        try:
            from app.core.self_awareness.temporal_self import temporal_self
            
            context = event.data.get("context", "")
            emotional_impact = event.data.get("emotional_impact", 0)
            person = event.data.get("person")
            
            # Only landmark highly significant interactions
            if emotional_impact > 0.5:
                temporal_self.record_landmark(
                    description=f"Significant moment: {context[:80]}",
                    category="interaction",
                    emotional_weight=emotional_impact,
                    people_involved=[person] if person else []
                )
                logger.debug(f"Marked temporal landmark for significant interaction")
        except Exception as e:
            logger.debug(f"Failed to mark landmark on significant interaction: {e}")
    
    # ===========================
    # ETHICAL TENSION HANDLERS
    # ===========================
    
    def _on_ethical_tension_update_self_model(self, event: AwarenessEvent) -> None:
        """Ethical tensions affect self-understanding."""
        try:
            from app.core.self_awareness.self_model import self_model
            
            content = event.data.get("content", "")
            category = event.data.get("category", "")
            
            self_model.update_self_model(
                trigger=f"Ethical tension: {category}",
                value_clarification=f"navigating {category}"
            )
            logger.debug(f"Self-model updated from ethical tension")
        except Exception as e:
            logger.debug(f"Failed to update self-model on ethical tension: {e}")
    
    def _on_ethical_tension_generate_thought(self, event: AwarenessEvent) -> None:
        """Generate thoughts when ethical tensions arise."""
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            content = event.data.get("content", "")
            category = event.data.get("category", "")
            
            thought = f"Something about this situation touches on {category}... I need to think about this."
            stream_of_consciousness.think(thought, "reflection")
            logger.debug(f"Generated thought about ethical tension")
        except Exception as e:
            logger.debug(f"Failed to generate thought on ethical tension: {e}")
    
    # ===========================
    # INSIGHT HANDLERS
    # ===========================
    
    def _on_insight_update_self_model(self, event: AwarenessEvent) -> None:
        """Insights may indicate new interests or growth."""
        try:
            from app.core.self_awareness.self_model import self_model
            
            insight = event.data.get("insight", "")
            
            # Extract potential new interest from insight
            if "about" in insight.lower():
                start = insight.lower().find("about") + 5
                topic = insight[start:start+30].strip().split()[0] if start < len(insight) else None
                if topic:
                    self_model.update_self_model(
                        trigger=f"Insight: {insight[:50]}",
                        new_interest=topic
                    )
                    logger.debug(f"Self-model updated from insight about {topic}")
        except Exception as e:
            logger.debug(f"Failed to update self-model on insight: {e}")
    
    # ===========================
    # MOOD CHANGE HANDLERS
    # ===========================
    
    def _on_mood_change_update_qualia(self, event: AwarenessEvent) -> None:
        """Mood changes affect subjective experience."""
        try:
            from app.core.inner_life.qualia import qualia_layer
            
            new_mood = event.data.get("new_mood", "")
            # Qualia layer auto-updates, just log
            experience = qualia_layer.get_current_experience()
            logger.debug(f"Qualia refreshed for mood: {new_mood}")
        except Exception as e:
            logger.debug(f"Failed to update qualia on mood change: {e}")
    
    # ===========================
    # SELF-MODEL UPDATE HANDLERS
    # ===========================
    
    def _on_self_model_update_consider_goal(self, event: AwarenessEvent) -> None:
        """Self-model changes may suggest new goals."""
        try:
            from app.core.goals.goal_system import goal_system
            
            aspect = event.data.get("aspect", "")
            current = event.data.get("current", "")
            
            # Interest changes may suggest learning goals
            if aspect == "interest":
                # Check if we already have a learning goal for this
                active_goals = goal_system.get_active_goals()
                already_tracked = any(current.lower() in g.description.lower() for g in active_goals)
                
                if not already_tracked:
                    goal_system.create_goal(
                        description=f"Explore my new interest in {current}",
                        category="learning",
                        priority=0.5,
                        motivation="This emerged from my self-understanding"
                    )
                    logger.debug(f"Created goal from self-model interest change")
        except Exception as e:
            logger.debug(f"Failed to consider goal on self-model update: {e}")
    
    # ===========================
    # TRUST CHANGE HANDLERS
    # ===========================
    
    def _on_trust_change_update_relationship(self, event: AwarenessEvent) -> None:
        """Trust changes should update relationship system."""
        try:
            from app.core.relationships.relationship_system import relationship_system
            
            entity = event.data.get("entity")
            old_level = event.data.get("old_level", 0.5)
            new_level = event.data.get("new_level", 0.5)
            
            if entity:
                delta = new_level - old_level
                if abs(delta) > 0.05:
                    reason = "trust grew" if delta > 0 else "trust challenged"
                    relationship_system.update_trust(entity, delta, reason)
                    logger.debug(f"Updated relationship trust for {entity}")
        except Exception as e:
            logger.debug(f"Failed to update relationship on trust change: {e}")
    
    # ===========================
    # MESSAGE_SENT HANDLERS (Phase: States and Actions Coherence)
    # ===========================
    
    def _on_message_sent_check_intention_progress(self, event: AwarenessEvent) -> None:
        """When a message is sent, check if it advances any active intentions."""
        try:
            from app.core.agency.intention_engine import intention_engine
            
            message_content = event.data.get("content", "")
            context = event.data.get("context", {})
            
            if not message_content:
                return
            
            # Get active intentions
            active_intentions = intention_engine.get_active_intentions()[:5]
            message_words = set(message_content.lower().split())
            
            for intention in active_intentions:
                # Check if message content relates to intention
                intention_words = set(intention.content.lower().split())
                
                # Remove common words
                stop_words = {"the", "a", "an", "is", "are", "to", "for", "of", "and", "i", "you", "my"}
                intention_words -= stop_words
                message_words_filtered = message_words - stop_words
                
                overlap = len(intention_words & message_words_filtered)
                
                if overlap >= 2:  # At least 2 meaningful words overlap
                    # Record progress on this intention
                    progress_note = f"Discussed in conversation: {message_content[:50]}..."
                    intention_engine.pursue_intention(intention.id, progress_note)
                    logger.debug(f"📝 Intention progress: {intention.content[:40]}...")
                    break  # Only record one intention per message
                    
        except Exception as e:
            logger.debug(f"Failed to check intention progress on message sent: {e}")
    
    # ===========================
    # GOAL PROGRESS → PROACTIVE SHARING (Phase: States and Actions Coherence)
    # ===========================
    
    def _on_goal_progress_consider_sharing(self, event: AwarenessEvent) -> None:
        """When goals reach milestones, consider proactive sharing."""
        try:
            new_progress = event.data.get("new_progress", 0)
            old_progress = event.data.get("old_progress", 0)
            description = event.data.get("description", "")
            goal_id = event.data.get("goal_id", "")
            
            # Check for milestone crossings (25%, 50%, 75%, 100%)
            milestones = [0.25, 0.50, 0.75, 1.0]
            
            for milestone in milestones:
                if old_progress < milestone <= new_progress:
                    # Crossed a milestone!
                    logger.info(f"🎯 Goal milestone: {description[:40]}... reached {milestone:.0%}")
                    
                    # Add to initiative engine's triggers
                    try:
                        from app.core.proactive.initiative_engine import initiative_engine
                        
                        # Record the milestone for potential proactive sharing
                        initiative_engine.record_goal_milestone(
                            goal_id=goal_id,
                            milestone=milestone,
                            description=description
                        )
                    except Exception as ie:
                        logger.debug(f"Failed to record goal milestone in initiative engine: {ie}")
                    
                    # Generate a thought about the progress
                    try:
                        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
                        
                        if milestone == 1.0:
                            thought = f"I completed a goal: {description[:60]}... I want to share this!"
                        else:
                            thought = f"I'm making progress ({milestone:.0%}) on: {description[:60]}..."
                        
                        stream_of_consciousness.think(thought, "reflection")
                    except Exception as se:
                        logger.debug(f"Failed to generate thought about goal progress: {se}")
                    
                    break  # Only handle one milestone per event
                    
        except Exception as e:
            logger.debug(f"Failed to consider sharing on goal progress: {e}")


# Singleton instance
bus_subscribers = BusSubscriberRegistry()


def initialize_bus_subscribers() -> int:
    """
    Initialize all bus subscribers.
    Call this once at application startup.
    
    Returns:
        Number of subscriptions registered
    """
    return bus_subscribers.register_all_subscribers()
