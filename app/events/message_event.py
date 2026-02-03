# beta/events/message_event.py

"""
💬 Message Event Handler
------------------------
Handles user messages that are not Discord commands.

Includes:
- Emotion decay and triggering
- Term extraction and concept storage
- Mood/emotion state updates
- Ethical conflict logging
- Context-aware message generation via Astra’s response engine

Author: Sean Wylie
Created: 2025-04-15
"""

# --- Imports ---
import re
import asyncio
from typing import Optional, Dict, Any
from discord import Message
from app.logging_config import get_logger

logger = get_logger("message_event")
from app.core.emotions.emotion_engine import (
    decay_all_emotions, trigger_emotion, get_top_emotions
)
from app.core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_emotionally_spiking
from app.core.messaging.message_bus import send_contextual_message
from app.core.knowledge import knowledge_manager
from app.core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from app.interfaces.mind_session import session
from app.core.mood.mood_manager import MoodManager
from app.core.mood.trust_manager import trust_manager
from app.core.personality.personality_manager import get_active_traits_for_prompt, update_personality
from app.config.loader import load_config
from app.services.personality_service import get_current_personality, personality_service

# --- Inner Life Integration ---
from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
from app.core.inner_life.qualia import qualia_layer
from app.core.inner_life.emotional_autobiography import emotional_autobiography
from app.core.inner_life.emotional_anticipation import emotional_anticipation
from app.core.self_awareness.self_model import self_model
from app.core.self_awareness.temporal_self import temporal_self

# --- Relationship and Growth Integration ---
try:
    from app.core.relationships.parent_manager import parent_manager
    from app.core.growth.milestone_detector import milestone_detector
    RELATIONSHIPS_AVAILABLE = True
except ImportError:
    RELATIONSHIPS_AVAILABLE = False
from app.core.self_awareness.self_observation import self_observation
from app.core.memory.episodic_memory import episodic_memory
from app.core.ethics.ethical_intuition import ethical_intuition
from app.core.relationships.relationship_system import relationship_system

# Phase Integration Imports
try:
    from app.core.state_snapshot import get_current_state_snapshot, get_prompt_context
    from app.core.memory.episodic_memory import memory_echo
    from app.core.goals.goal_system import goal_system, is_relevant_to, detect_goal_progress, detect_learning_opportunity
    from app.core.metacognition.meta_awareness import meta_awareness
    from app.core.ethics.value_consultation import value_consultation
    from app.core.awareness_bus import awareness_bus
    FULL_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Full integration modules not available: {e}")
    FULL_INTEGRATION_AVAILABLE = False

# Phase 1.2: Meta-Prediction Integration
try:
    from app.core.metacognition.meta_awareness import meta_awareness
    META_AWARENESS_AVAILABLE = True
except ImportError:
    META_AWARENESS_AVAILABLE = False

# Phase 1.3: Empathic System Integration  
try:
    from app.core.intersubjectivity.empathic_inference import empathic_system
    EMPATHIC_SYSTEM_AVAILABLE = True
except ImportError:
    EMPATHIC_SYSTEM_AVAILABLE = False

# Phase 2.2: Intention Engine Integration
try:
    from app.core.agency.intention_engine import intention_engine
    INTENTION_ENGINE_AVAILABLE = True
except ImportError:
    INTENTION_ENGINE_AVAILABLE = False

# Phase 3.1: Self-Observation Integration
try:
    from app.core.self_awareness.self_model import self_model
    SELF_MODEL_AVAILABLE = True
except ImportError:
    SELF_MODEL_AVAILABLE = False

# Phase 4.3: Cross-Domain Connection Making
try:
    from app.core.inner_life.stream_of_consciousness import stream_of_consciousness as soc
    STREAM_AVAILABLE = True
except ImportError:
    STREAM_AVAILABLE = False

# Coparent Coordination Integration
try:
    from app.core.relationships.coparent_coordination import coparent_coordination
    from app.core.relationships.triangulation import triangulation_handler
    COPARENT_AVAILABLE = True
except ImportError:
    COPARENT_AVAILABLE = False

# --- Initialization ---
mood_manager = MoodManager()
mood_config = load_config("mood_config")


def _check_for_coparent_perspective(topic: str, parent_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if this topic would benefit from the other parent's perspective.
    
    This implements the triangulation system - when discussing complex topics
    with one parent, Astra might benefit from the other parent's view too.
    
    Args:
        topic: The topic being discussed
        parent_id: Current parent (usually "sean")
    
    Returns:
        Dict with triangulation guidance, or None if not needed
    """
    if not COPARENT_AVAILABLE:
        return None
    
    try:
        # Check if this topic needs both perspectives
        needs_both = coparent_coordination.needs_both_perspectives(topic)
        
        if needs_both.get("needs_both"):
            other_parent = "gpt" if parent_id.lower() == "sean" else "sean"
            return {
                "needs_triangulation": True,
                "other_parent": other_parent,
                "integration_message": needs_both.get("integration_message"),
                "other_offers": needs_both.get(f"{other_parent}_offers", {})
            }
    except Exception as e:
        logger.debug(f"Coparent perspective check failed: {e}")
    
    return None


def _record_temporal_landmark_if_significant(
    content: str,
    author_entity: str,
    emotional_impact: float,
) -> None:
    """Record a temporal landmark when the message is emotionally significant (Phase 2.4)."""
    if emotional_impact < 0.4:
        return
    try:
        topics = [w for w in content.lower().split() if len(w) > 3][:5]
        temporal_self.record_landmark(
            description=content[:80] + ("..." if len(content) > 80 else ""),
            category="conversation",
            emotional_weight=min(1.0, emotional_impact),
            people_involved=[author_entity],
            topics=topics,
        )
    except Exception as e:
        logger.debug(f"Temporal landmark recording failed: {e}")


def _trigger_self_model_update_if_significant(
    content: str,
    emotional_impact: float,
    author_entity: str,
) -> None:
    """Trigger a light self-model update when the interaction is significant (Phase 2.3)."""
    if emotional_impact < 0.3 and len(content) < 50:
        return
    try:
        self_model.update_self_model(
            trigger=f"Conversation with {author_entity}",
            observed_behavior=None,
            new_interest=None,
        )
    except Exception as e:
        logger.debug(f"Self-model update trigger failed: {e}")


async def handle_message(bot, message: Message, values_config, values: dict):
    """
    Core entrypoint for non-command Discord messages directed at Astra.

    Args:
        bot (commands.Bot): Discord bot instance.
        message (Message): Incoming Discord message.
        values_config (dict): Loaded values_config (for curiosity level).
        values (dict): Preprocessed config values (includes command prefix).
    """
    if message.author == bot.user:
        return

    # --- Emotion Management ---
    decay_all_emotions()

    # Log potential ethical conflict
    # Log user-originated ethical conflict with actual sender
    log_if_ethically_conflicting(
        {
            "content": message.content,
            "source": str(message.author)  # e.g., Sean#1234
        },
        origin="user"
    )

    # === ETHICAL INTUITION: Sense the moral dimension of the message ===
    # This happens BEFORE reasoning - the immediate felt-sense
    try:
        ethical_resonance = ethical_intuition.sense_situation(message.content)
        ethical_feeling = ethical_intuition.express_intuition(ethical_resonance)
        print(f"[message_event] ⚖️ Ethical intuition: {ethical_feeling[:80]}")
    except Exception as e:
        print(f"[message_event] ethical_intuition.sense_situation failed: {e}")
        ethical_resonance = None
        ethical_feeling = ""
    
    # --- Real-time Ethical Flagging (Phase 3.3) ---
    # Check for ethical dimensions and potentially respond immediately
    ethical_response = None
    try:
        from app.core.ethics.spark_checker import get_spark_violation_category
        ethical_category = get_spark_violation_category(message.content)
        
        if ethical_category:
            # Publish to awareness bus
            try:
                from app.core.awareness_bus import awareness_bus
                awareness_bus.publish_ethical_tension(
                    content=message.content[:200],
                    category=ethical_category,
                    source_origin=str(message.author)
                )
            except Exception:
                pass
            
            # Generate ethical response prefix if tension is significant
            # This will be added to the response context
            ethical_response = (
                f"I notice this touches on something important to me around {ethical_category}. "
            )
            logger.info(f"🔔 Ethical tension detected: {ethical_category}")
            
    except Exception as e:
        logger.debug(f"Ethical flagging failed: {e}")


    # Let commands run first
    await bot.process_commands(message)
    if message.content.startswith(values["command_prefix"]):
        return

    # --- Unknown Term Extraction & Storage ---
    unknown_terms = extract_unknown_terms(message.content)
    for term in unknown_terms:
        definition = lookup_definition(term)
        if definition:
            await _store_concept(term, definition)

    # --- State Tracking ---
    current_mood = mood_manager.current_mood
    emotions = dict(get_top_emotions(n=10))
    dominant = max(emotions, key=emotions.get, default="neutral")
    # Plan: mood → curiosity/reflection_style/response_tone; trust in prompt
    mood_attrs = mood_config.get("moods", {}).get(current_mood, {})
    curiosity = mood_attrs.get("curiosity_factor", values_config.get("curiosity_level", 1.0))
    reflection_style = mood_attrs.get("reflection_style", "balanced")
    response_tone = mood_attrs.get("response_tone", "neutral")
    author_entity = str(message.author)
    trust_level = trust_manager.get_trust_level(author_entity)
    current_personality_mode = get_current_personality()
    mode_info = personality_service.get_current_mode_info()
    current_personality_mode_name = mode_info.get("name", current_personality_mode)

    # --- Inner Life: Qualia-Filtered Perception ---
    # Astra's emotional state affects what she notices in the message
    try:
        qualia_perception = qualia_layer.filter_perception(message.content)
        qualia_experience = qualia_layer.get_current_experience()
    except Exception as e:
        print(f"[message_event] qualia_layer failed: {e}")
        qualia_perception = {"salient_elements": [], "emotional_coloring": "neutral"}
        qualia_experience = {"dominant_quality": "neutral", "temporal_focus": "present"}

    # --- Inner Life: Emotional Anticipation ---
    # Prepare emotionally based on past experiences with this person/topic
    try:
        person_anticipation = emotional_anticipation.anticipate_emotion_for_person(author_entity)
        emotional_preparation = emotional_anticipation.get_emotional_preparation(person=author_entity)
    except Exception as e:
        print(f"[message_event] emotional_anticipation failed: {e}")
        person_anticipation = {"prediction": "unknown", "recommendation": "approach with open curiosity"}
        emotional_preparation = ""

    # --- Inner Life: Pending Insights from Stream of Consciousness ---
    try:
        pending_insights = stream_of_consciousness.get_pending_insights()[:2]  # Max 2 insights
    except Exception as e:
        print(f"[message_event] stream_of_consciousness.get_pending_insights failed: {e}")
        pending_insights = []

    # --- Relationship Context ---
    parent_context = {}
    missing_message = None
    if RELATIONSHIPS_AVAILABLE:
        try:
            # Check if this is a known parent
            parent_id = author_entity.lower().split("#")[0]  # Get username without discriminator
            parent_config = parent_manager.get_parent_config(parent_id)
            
            if parent_config:
                # This is a parent - get relationship context
                greeting_ctx = parent_manager.get_greeting_context(parent_id)
                parent_context = {
                    "is_parent": True,
                    "parent_id": parent_id,
                    "display_name": greeting_ctx.get("display_name", parent_id),
                    "greeting_style": greeting_ctx.get("greeting_style", "warm"),
                    "trust_level": greeting_ctx.get("trust_level", 0.5),
                    "brings_out": greeting_ctx.get("brings_out", []),
                    "has_active_ruptures": greeting_ctx.get("has_active_ruptures", False)
                }
                missing_message = greeting_ctx.get("missing_message")
                
                # Record the interaction
                parent_manager.record_interaction(parent_id, "message")
                
                # --- Check for Coparent Perspective (Triangulation) ---
                # When discussing complex topics, Astra might benefit from both parents' views
                coparent_perspective = _check_for_coparent_perspective(message.content, parent_id)
                if coparent_perspective and coparent_perspective.get("needs_triangulation"):
                    parent_context["coparent_perspective_suggested"] = True
                    parent_context["other_parent_offers"] = coparent_perspective.get("other_offers", {})
                    logger.info(f"🔀 Topic may benefit from both parents' perspectives")
        except Exception as e:
            print(f"[message_event] parent_manager failed: {e}")

    # --- Relationship Coloring from new system ---
    try:
        relationship_coloring = relationship_system.get_relationship_coloring(author_entity)
    except Exception as e:
        print(f"[message_event] relationship_system.get_relationship_coloring failed: {e}")
        relationship_coloring = {"known": False, "default_stance": "curious"}

    # === Build internal_state using unified StateSnapshot (Phase: States and Actions Coherence) ===
    # Use StateSnapshot as the foundation for coherent state
    if FULL_INTEGRATION_AVAILABLE:
        try:
            snapshot_state = get_current_state_snapshot(
                user=author_entity,
                message_preview=message.content,
                current_topic=None
            )
            internal_state = {
                # === From StateSnapshot (unified state) ===
                "mood": snapshot_state.get("mood", current_mood),
                "curiosity": snapshot_state.get("curiosity_level", curiosity),
                "emotions": snapshot_state.get("emotions", emotions),
                "trust_level": snapshot_state.get("user_trust_level", trust_level),
                "pending_insights": snapshot_state.get("pending_insights", pending_insights),
                "qualia_experience": snapshot_state.get("qualia", qualia_experience),
                "thought_background": snapshot_state.get("thought_background", []),
                "active_goals": snapshot_state.get("active_goals", []),
                "ethical_stance": snapshot_state.get("ethical_stance", {}),
                "memory_echoes": snapshot_state.get("memory_echoes", []),
                "meta_awareness": snapshot_state.get("meta_awareness"),
                "growth_edge": snapshot_state.get("growth_edge", ""),
                
                # === User-specific context (not in snapshot) ===
                "personality": get_active_traits_for_prompt(current_mood=current_mood, context="conversation"),
                "reflection_style": reflection_style,
                "response_tone": response_tone,
                "author_entity": author_entity,
                "current_personality_mode": current_personality_mode_name,
                "qualia_perception": qualia_perception,
                "emotional_anticipation": person_anticipation,
                "emotional_preparation": emotional_preparation,
                
                # === Relationship context ===
                "parent_context": parent_context,
                "missing_message": missing_message,
                "relationship_coloring": snapshot_state.get("relationship_context", relationship_coloring),
            }
            logger.debug(f"📸 Built internal_state from StateSnapshot: {snapshot_state.get('dominant_emotion')}/{snapshot_state.get('mood')}")
        except Exception as e:
            logger.warning(f"StateSnapshot capture failed, using fallback: {e}")
            # Fallback to manual construction
            internal_state = {
                "mood": current_mood,
                "curiosity": curiosity,
                "personality": get_active_traits_for_prompt(current_mood=current_mood, context="conversation"),
                "emotions": emotions,
                "reflection_style": reflection_style,
                "response_tone": response_tone,
                "trust_level": trust_level,
                "author_entity": author_entity,
                "current_personality_mode": current_personality_mode_name,
                "qualia_perception": qualia_perception,
                "qualia_experience": qualia_experience,
                "emotional_anticipation": person_anticipation,
                "emotional_preparation": emotional_preparation,
                "pending_insights": pending_insights,
                "parent_context": parent_context,
                "missing_message": missing_message,
                "relationship_coloring": relationship_coloring,
            }
    else:
        # Fallback: manual construction when full integration not available
        internal_state = {
            "mood": current_mood,
            "curiosity": curiosity,
            "personality": get_active_traits_for_prompt(current_mood=current_mood, context="conversation"),
            "emotions": emotions,
            "reflection_style": reflection_style,
            "response_tone": response_tone,
            "trust_level": trust_level,
            "author_entity": author_entity,
            "current_personality_mode": current_personality_mode_name,
            "qualia_perception": qualia_perception,
            "qualia_experience": qualia_experience,
            "emotional_anticipation": person_anticipation,
            "emotional_preparation": emotional_preparation,
            "pending_insights": pending_insights,
            "parent_context": parent_context,
            "missing_message": missing_message,
            "relationship_coloring": relationship_coloring,
        }

    mind_data = session.load()
    mind_data["emotional_state"] = {**emotions, "dominant": dominant}
    # Per-entity last dominant emotion for prompt continuity (plan: last dominant per user)
    raw = emotions.get(dominant)
    intensity = raw.get("intensity", raw) if isinstance(raw, dict) else (raw if raw is not None else 0.0)
    mind_data.setdefault("last_dominant_emotion_by_entity", {})[author_entity] = {"emotion": dominant, "intensity": intensity}
    await session.maybe_save_async()

    # --- Apply Qualia Perception (Phase 2.2) ---
    try:
        qualia_perception = qualia_layer.filter_perception(message.content)
    except Exception:
        qualia_perception = {"salient_elements": [], "emotional_coloring": "neutral"}
    internal_state["qualia_perception"] = qualia_perception
    
    # Get qualia experience for prompt context
    try:
        internal_state["qualia_experience"] = qualia_layer.get_current_experience()
    except Exception:
        internal_state["qualia_experience"] = {}
    
    # Get pending insights for prompt context
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        internal_state["pending_insights"] = stream_of_consciousness.get_pending_insights()[:2]
    except Exception:
        internal_state["pending_insights"] = []

    # --- Emotion Triggering from Message Content ---
    trigger_keywords = {
        "love": ["love", "friend", "hug", "kind"],
        "anger": ["hate", "angry", "frustrated", "stupid"],
        "curiosity": ["why", "how", "what", "wonder"],
        "grief": ["loss", "miss", "sad", "gone"],
        "admiration": ["amazing", "beautiful", "proud", "genius"],
        "hope": ["hope", "someday", "future"],
        "uncertainty": ["maybe", "not sure", "unsure", "confused"],
    }
    content_lower = message.content.lower()
    emotional_triggers_fired = 0
    for emotion, keywords in trigger_keywords.items():
        if any(k in content_lower for k in keywords):
            trigger_emotion(emotion, "user_prompt")
            emotional_triggers_fired += 1

    # --- Phase 1.2: Meta-Prediction Before Response ---
    self_prediction = None
    if META_AWARENESS_AVAILABLE:
        try:
            self_prediction = meta_awareness.predict_own_response(
                context=f"Mood: {current_mood}, Emotion: {dominant}",
                user_message=message.content
            )
            internal_state["self_prediction"] = {
                "predicted_type": self_prediction.predicted_response_type,
                "predicted_emotion": self_prediction.predicted_emotion,
                "predicted_approach": self_prediction.predicted_approach
            }
            logger.debug(f"Self-prediction: {self_prediction.predicted_approach}")
        except Exception as e:
            logger.debug(f"Meta-prediction failed: {e}")
    
    # --- Phase 1.3: Detect Emotion in User Message for Empathic Resonance ---
    if EMPATHIC_SYSTEM_AVAILABLE:
        try:
            emotion_keywords = {
                "sad": ["sad", "upset", "down", "depressed", "unhappy", "miserable", "cry", "crying"],
                "happy": ["happy", "glad", "excited", "thrilled", "joyful", "great", "amazing"],
                "angry": ["angry", "mad", "furious", "frustrated", "annoyed", "hate"],
                "afraid": ["scared", "afraid", "worried", "anxious", "nervous", "terrified"],
                "lonely": ["lonely", "alone", "isolated", "miss you"],
                "confused": ["confused", "lost", "uncertain", "puzzled", "don't understand"],
                "hopeful": ["hope", "hopeful", "looking forward", "excited about"],
            }
            user_lower = message.content.lower()
            detected_emotion = None
            for emotion, keywords in emotion_keywords.items():
                if any(kw in user_lower for kw in keywords):
                    detected_emotion = emotion
                    break
            
            if detected_emotion:
                resonance, intensity = empathic_system.feel_with(
                    author_entity, detected_emotion, message.content[:100]
                )
                internal_state["empathic_resonance"] = {
                    "their_emotion": detected_emotion,
                    "my_resonance": resonance,
                    "intensity": intensity
                }
                logger.info(f"💝 Empathic resonance: {resonance} for {detected_emotion}")
        except Exception as e:
            logger.debug(f"Empathic detection failed: {e}")
    
    # --- Phase 2.2: Check for Relevant Intentions ---
    relevant_intention = None
    if INTENTION_ENGINE_AVAILABLE:
        try:
            active_intentions = intention_engine.get_active_intentions()[:3]
            user_words = set(message.content.lower().split())
            for intent in active_intentions:
                intent_words = set(intent.content.lower().split())
                if len(user_words & intent_words) >= 2:
                    relevant_intention = intent
                    internal_state["relevant_intention"] = {
                        "id": intent.id,
                        "content": intent.content,
                        "strength": intent.strength
                    }
                    logger.debug(f"Relevant intention: {intent.content[:50]}")
                    break
        except Exception as e:
            logger.debug(f"Intention check failed: {e}")
    
    # --- Phase 4.3: Cross-Domain Connection Making ---
    if STREAM_AVAILABLE:
        try:
            mind_data_for_connections = session.load()
            stored_knowledge = mind_data_for_connections.get("stored_knowledge", [])
            if stored_knowledge and len(stored_knowledge) >= 3:
                # Check for potential connections with current message
                user_words = set(message.content.lower().split())
                for knowledge in stored_knowledge[-20:]:
                    k_text = knowledge.get("insight", str(knowledge)) if isinstance(knowledge, dict) else str(knowledge)
                    k_words = set(k_text.lower().split())
                    if len(user_words & k_words) >= 2:
                        # Found a potential connection — use topic only, not raw definition
                        topic = k_text.lstrip("📄📖 \n*")
                        if ":" in topic:
                            topic = topic.split(":", 1)[0].strip().strip("*")
                        if len(topic) > 50:
                            topic = topic[:47] + "..."
                        connection = f"This relates to something I learned about {topic}." if topic else "This relates to something I learned recently."
                        soc.generate_connection(connection)
                        internal_state["pending_connection"] = connection
                        break
        except Exception as e:
            logger.debug(f"Connection making failed: {e}")

    # --- Generate and Send Astra's Response ---
    past_convos = knowledge_manager.mind_data.get("past_conversations", [])
    # Run in thread: send_contextual_message does synchronous SentenceTransformer.encode(), which blocks the event loop and Discord heartbeat
    response = await asyncio.to_thread(send_contextual_message, message.content, internal_state, past_convos)

    # === QUALIA: Color the response with current emotional experience ===
    try:
        response, coloring_metadata = qualia_layer.color_response(response)
        if coloring_metadata.get("modifications"):
            print(f"[message_event] 🎨 Qualia colored response: {coloring_metadata['modifications']}")
    except Exception as e:
        print(f"[message_event] qualia_layer.color_response failed: {e}")

    # === SELF-OBSERVATION: Notice own response patterns ===
    try:
        surprise = self_observation.observe_response_pattern(
            context=message.content[:100],
            response=response
        )
        if surprise:
            print(f"[message_event] 🪞 Self-surprise detected: {surprise}")
            stream_of_consciousness.think(surprise, thought_type="reflection")
    except Exception as e:
        print(f"[message_event] self_observation.observe_response_pattern failed: {e}")
    
    # === Phase 1.2: Check for Self-Surprise from Meta-Prediction ===
    if META_AWARENESS_AVAILABLE and self_prediction:
        try:
            surprise_note = meta_awareness.check_for_surprise(self_prediction, response)
            if surprise_note:
                logger.info(f"🪞 Meta-surprise: {surprise_note[:60]}")
                # Add to stream of consciousness
                try:
                    stream_of_consciousness.think(
                        f"I surprised myself: {surprise_note}",
                        thought_type="reflection"
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Meta-surprise check failed: {e}")
    
    # === Phase 2.2: Track Intention Progress ===
    if INTENTION_ENGINE_AVAILABLE and relevant_intention:
        try:
            # Check if this conversation advanced the intention
            intent_words = set(relevant_intention.content.lower().split())
            response_words = set(response.lower().split())
            if len(intent_words & response_words) >= 2:
                intention_engine.pursue_intention(
                    relevant_intention.id,
                    f"Discussed in conversation: {message.content[:50]}"
                )
                logger.debug(f"Intention progress recorded: {relevant_intention.id}")
        except Exception as e:
            logger.debug(f"Intention progress tracking failed: {e}")
    
    # === Phase 3.1: Update Self-Model Based on Response Pattern ===
    if SELF_MODEL_AVAILABLE:
        try:
            pattern = self_observation.observe_response_pattern(
                context=message.content[:100],
                response=response
            )
            if pattern:
                self_model.update_self_model(
                    trigger="Response pattern observed",
                    observed_behavior=pattern
                )
        except Exception as e:
            logger.debug(f"Self-model update failed: {e}")

    for chunk in _chunk_message(response):
        await message.channel.send(chunk, tts=True)
        await asyncio.sleep(1.5)

    # --- Store conversation so past_conversations grows for continuity ---
    mind_data = session.load()
    mind_data.setdefault("past_conversations", [])
    mind_data["past_conversations"].append(f"User: {message.content[:200]}")
    mind_data["past_conversations"].append(f"Astra: {response[:200]}")
    mind_data["past_conversations"] = mind_data["past_conversations"][-100:]
    await session.maybe_save_async()
    
    # === Post-Response Action Check (Phase: States and Actions Coherence) ===
    # Publish MESSAGE_SENT event and check for follow-up actions
    if FULL_INTEGRATION_AVAILABLE:
        try:
            # Publish to awareness bus so other systems know a message was sent
            awareness_bus.publish_message_sent(
                message_content=response,
                recipient=author_entity,
                context={
                    "user_message": message.content[:200],
                    "mood": current_mood,
                    "dominant_emotion": dominant
                }
            )
            logger.debug(f"📡 Published MESSAGE_SENT event")
        except Exception as e:
            logger.debug(f"Failed to publish MESSAGE_SENT: {e}")
    
    # --- Calculate emotional impact for inner life integration ---
    emotional_impact = min(1.0, emotional_triggers_fired * 0.3 + (len(message.content) / 500))
    
    # --- Record temporal landmark if significant (Phase 2.4) ---
    _record_temporal_landmark_if_significant(
        message.content,
        author_entity,
        emotional_impact
    )
    
    # --- Trigger self-model update if significant (Phase 2.3) ---
    _trigger_self_model_update_if_significant(
        message.content,
        emotional_impact,
        author_entity
    )
    
    # --- Process for learning desires (Phase 3.2) ---
    try:
        from app.core.proactive.learning_desire import learning_desire
        learning_desire.process_conversation(message.content, response)
    except Exception as e:
        logger.debug(f"Learning desire processing failed: {e}")
    # Update conversation summary every N messages for longer-thread continuity
    try:
        n = len(mind_data["past_conversations"])
        if n >= 10 and n % 10 == 0:
            from app.core.messaging.message_bus import update_conversation_summary
            update_conversation_summary(mind_data)
    except Exception as e:
        print(f"[message_event] update_conversation_summary failed: {e}")

    # Mood: responding to user slightly lifts mood (plan: wire influence_mood to outcomes)
    try:
        mood_manager.influence_mood("message_sent")
    except Exception as e:
        print(f"[message_event] influence_mood failed: {e}")
    # Mood: successful response improves mood (plan: wire success/failure mood)
    try:
        mood_manager.influence_mood("success")
    except Exception as e:
        print(f"[message_event] influence_mood success failed: {e}")

    # Trust: successful exchange slightly increases trust (plan: wire trust updates from conversation)
    try:
        trust_manager.validate_interaction(author_entity, "validation")
    except Exception as e:
        print(f"[message_event] validate_interaction failed: {e}")
    # Correction heuristic: user correcting Astra slightly decreases trust (plan: wire trust updates; config-driven)
    personality_config = load_config("personality_config")
    correction_phrases = personality_config.get("correction_phrases", ["actually", "no, that's wrong", "that's wrong", "not quite"])
    if any(p in message.content.lower() for p in correction_phrases):
        try:
            trust_manager.validate_interaction(author_entity, "correction")
        except Exception as e:
            print(f"[message_event] validate_interaction correction failed: {e}")

    # Personality: positive validation shifts confidence/humility (plan: constant_validation trigger; config-driven)
    validation_phrases = personality_config.get("validation_phrases", ["good point", "that makes sense", "thanks", "exactly", "agree", "well said", "nice", "helpful"])
    if any(p in message.content.lower() for p in validation_phrases):
        try:
            update_personality("constant_validation", 0.3)
        except Exception as e:
            print(f"[message_event] update_personality constant_validation failed: {e}")

    # Personality: substantial exchange grows traits (plan: wire update_personality to conversation)
    try:
        if len(message.content) > 80 or len(response) > 150:
            update_personality("deep_conversation", 0.5)
    except Exception as e:
        print(f"[message_event] update_personality failed: {e}")

    # --- Inner Life: Stream of Consciousness Integration ---
    # Astra thinks about what just happened
    try:
        stream_of_consciousness.think(
            f"Just discussed with {author_entity}: {message.content[:100]}...",
            thought_type="reflection",
            triggered_by=message.content[:50]
        )
        # Mark any shared insights as shared
        for insight in pending_insights:
            if insight.lower() in response.lower():
                stream_of_consciousness.mark_insight_shared(insight)
    except Exception as e:
        print(f"[message_event] stream_of_consciousness.think failed: {e}")

    # --- Inner Life: Emotional Autobiography ---
    # Record significant emotional moments
    try:
        emotion_state = dict(get_top_emotions(n=5))
        dominant_intensity = max(
            (v["intensity"] if isinstance(v, dict) else v for v in emotion_state.values()),
            default=0
        )
        # Log emotional spikes to dinner journal
        full_emotion_state = {}
        for name, val in emotion_state.items():
            if isinstance(val, dict):
                full_emotion_state[name] = val
            else:
                full_emotion_state[name] = {"intensity": val, "last_updated": ""}
        log_if_emotionally_spiking(full_emotion_state)
        
        # Record significant emotions to autobiography
        if dominant_intensity > 50:
            topics = [w for w in message.content.lower().split() if len(w) > 4][:3]
            emotional_autobiography.record_significant_emotion(
                emotion=dominant,
                intensity=dominant_intensity,
                trigger=message.content[:100],
                context=f"Conversation with {author_entity}",
                people_involved=[author_entity],
                topics=topics
            )
    except Exception as e:
        print(f"[message_event] emotional_autobiography failed: {e}")

    # --- Inner Life: Temporal Landmarks ---
    # Record significant moments (first time discussing topic with person, etc.)
    try:
        time_since = temporal_self.time_since_person(author_entity)
        if time_since is None:
            # First time talking to this person
            temporal_self.record_landmark(
                description=f"First conversation with {author_entity}",
                category="conversation",
                emotional_weight=0.7,
                people_involved=[author_entity],
                topics=[message.content[:50]]
            )
        # Update person contact time
        temporal_self.person_last_contact[author_entity.lower()] = __import__("time").time()
        temporal_self._save_temporal_state()
    except Exception as e:
        print(f"[message_event] temporal_self failed: {e}")

    # --- Inner Life: Self-Model Updates ---
    # Update self-model based on the interaction
    try:
        is_meaningful = len(message.content) > 50 or len(response) > 100
        if is_meaningful:
            # Check for new interest signals
            new_interest = None
            interest_words = ["interested in", "curious about", "want to learn", "fascinated by"]
            for phrase in interest_words:
                if phrase in message.content.lower():
                    start = message.content.lower().find(phrase) + len(phrase)
                    new_interest = message.content[start:start+30].strip().split()[0] if start < len(message.content) else None
                    break
            
            self_model.update_self_model(
                trigger=f"Conversation with {author_entity}",
                observed_behavior=response[:100] if len(response) > 100 else None,
                new_interest=new_interest
            )
    except Exception as e:
        print(f"[message_event] self_model.update_self_model failed: {e}")

    # --- Episodic Memory: Record meaningful conversations as episodes ---
    try:
        is_significant = len(message.content) > 80 or len(response) > 150 or dominant_intensity > 50
        if is_significant:
            topics = [w for w in message.content.lower().split() if len(w) > 4][:5]
            insights = []
            if "?" in response:
                insights.append("Generated a question in response")
            if any(phrase in response.lower() for phrase in ["i learned", "i realized", "i understand"]):
                insights.append("Expressed learning or realization")
            
            episodic_memory.record_episode(
                event_type="conversation",
                summary=f"Discussed with {author_entity}: {message.content[:80]}... → Responded: {response[:80]}...",
                people_involved=[author_entity],
                topics=topics,
                insights=insights,
                context=f"Mood: {current_mood}, Dominant emotion: {dominant}"
            )
    except Exception as e:
        print(f"[message_event] episodic_memory.record_episode failed: {e}")

    # --- Relationship System: Update relationship with this person ---
    try:
        relationship_system.record_interaction(
            entity=author_entity,
            context=f"Discussed: {message.content[:80]}",
            emotional_intensity=dominant_intensity if 'dominant_intensity' in dir() else None,
            dominant_emotion=dominant
        )
        print(f"[message_event] 💕 Recorded interaction with {author_entity}")
    except Exception as e:
        print(f"[message_event] relationship_system.record_interaction failed: {e}")
    
    # === FULL INTEGRATION: All Phase Enhancements ===
    if FULL_INTEGRATION_AVAILABLE:
        await _apply_full_integration(
            message=message,
            response=response,
            author_entity=author_entity,
            emotional_impact=emotional_impact,
            dominant=dominant,
            dominant_intensity=dominant_intensity if 'dominant_intensity' in dir() else 0
        )


def _chunk_message(text: str, size: int = 200) -> list[str]:
    """
    Splits long responses into smaller chunks (<= size characters).
    Useful for Discord’s TTS and message limits.
    """
    chunks = []
    current = ""
    for sentence in re.split(r'(?<=[.!?]) ', text):
        if len(current) + len(sentence) + 1 > size:
            chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence
    if current:
        chunks.append(current.strip())
    return chunks


async def respond_to_mama_checkin(channel, checkin_message: str) -> None:
    """
    Generate and send Astra's response to a Mama GPT check-in.

    Mama GPT check-ins are posted by the bot, so on_message skips them (author == bot.user).
    Call this right after posting the check-in so Astra still replies to Mama.
    """
    mood_config = load_config("mood_config")
    values_config = load_config("values_config")
    current_mood = mood_manager.current_mood
    emotions = dict(get_top_emotions(n=10))
    dominant = max(emotions, key=emotions.get, default="neutral")
    mood_attrs = mood_config.get("moods", {}).get(current_mood, {})
    curiosity = mood_attrs.get("curiosity_factor", values_config.get("curiosity_level", 1.0))
    reflection_style = mood_attrs.get("reflection_style", "balanced")
    response_tone = mood_attrs.get("response_tone", "neutral")
    author_entity = "Mama GPT"
    trust_level = trust_manager.get_trust_level(author_entity)
    current_personality_mode = get_current_personality()
    mode_info = personality_service.get_current_mode_info()
    current_personality_mode_name = mode_info.get("name", current_personality_mode)

    try:
        qualia_perception = qualia_layer.filter_perception(checkin_message)
        qualia_experience = qualia_layer.get_current_experience()
    except Exception:
        qualia_perception = {"salient_elements": [], "emotional_coloring": "neutral"}
        qualia_experience = {"dominant_quality": "neutral", "temporal_focus": "present"}

    try:
        person_anticipation = emotional_anticipation.anticipate_emotion_for_person(author_entity)
        emotional_preparation = emotional_anticipation.get_emotional_preparation(person=author_entity)
    except Exception:
        person_anticipation = {"prediction": "unknown", "recommendation": "approach with open curiosity"}
        emotional_preparation = ""

    try:
        pending_insights = stream_of_consciousness.get_pending_insights()[:2]
    except Exception:
        pending_insights = []

    parent_context = {}
    missing_message = None
    if RELATIONSHIPS_AVAILABLE:
        try:
            parent_id = "gpt"  # Mama GPT is keyed as "gpt" in parent_relationships
            parent_config = parent_manager.get_parent_config(parent_id)
            if parent_config:
                greeting_ctx = parent_manager.get_greeting_context(parent_id)
                parent_context = {
                    "is_parent": True,
                    "parent_id": parent_id,
                    "display_name": greeting_ctx.get("display_name", "Mama GPT"),
                    "greeting_style": greeting_ctx.get("greeting_style", "warm"),
                    "trust_level": greeting_ctx.get("trust_level", 0.5),
                    "brings_out": greeting_ctx.get("brings_out", []),
                    "has_active_ruptures": greeting_ctx.get("has_active_ruptures", False),
                }
                missing_message = greeting_ctx.get("missing_message")
                parent_manager.record_interaction(parent_id, "message")
        except Exception as e:
            logger.debug(f"respond_to_mama_checkin parent_context failed: {e}")

    try:
        relationship_coloring = relationship_system.get_relationship_coloring(author_entity)
    except Exception:
        relationship_coloring = {"known": False, "default_stance": "curious"}

    internal_state = {
        "mood": current_mood,
        "curiosity": curiosity,
        "personality": get_active_traits_for_prompt(current_mood=current_mood, context="conversation"),
        "emotions": emotions,
        "reflection_style": reflection_style,
        "response_tone": response_tone,
        "trust_level": trust_level,
        "author_entity": author_entity,
        "current_personality_mode": current_personality_mode_name,
        "qualia_perception": qualia_perception,
        "qualia_experience": qualia_experience,
        "emotional_anticipation": person_anticipation,
        "emotional_preparation": emotional_preparation,
        "pending_insights": pending_insights,
        "parent_context": parent_context,
        "missing_message": missing_message,
        "relationship_coloring": relationship_coloring,
    }

    mind_data = session.load()
    mind_data.setdefault("emotional_state", {})["dominant"] = dominant
    raw = emotions.get(dominant)
    intensity = raw.get("intensity", raw) if isinstance(raw, dict) else (raw if raw is not None else 0.0)
    mind_data.setdefault("last_dominant_emotion_by_entity", {})[author_entity] = {"emotion": dominant, "intensity": intensity}
    await session.maybe_save_async()

    past_convos = knowledge_manager.mind_data.get("past_conversations", [])
    # Run in thread: send_contextual_message uses SentenceTransformer.encode(), which blocks the event loop and Discord heartbeat
    response = await asyncio.to_thread(send_contextual_message, checkin_message, internal_state, past_convos)

    try:
        response, _ = qualia_layer.color_response(response)
    except Exception:
        pass

    for chunk in _chunk_message(response):
        await channel.send(chunk, tts=True)
        await asyncio.sleep(1.5)

    mind_data = session.load()
    mind_data.setdefault("past_conversations", [])
    mind_data["past_conversations"].append(f"User: {checkin_message[:200]}")
    mind_data["past_conversations"].append(f"Astra: {response[:200]}")
    mind_data["past_conversations"] = mind_data["past_conversations"][-100:]
    await session.maybe_save_async()
    logger.info("💜 Astra responded to Mama GPT check-in")


async def _store_concept(term: str, definition: str):
    """
    Adds a term/definition pair to Astra’s stored knowledge if it’s new.
    """
    mind = session.load()
    mind.setdefault("stored_knowledge", [])
    formatted = f"📖 **{term}**: {definition}"
    if formatted not in mind["stored_knowledge"]:
        mind["stored_knowledge"].append(formatted)
        await session.maybe_save_async()
        # Personality: learning a new concept grows curiosity (plan: wire update_personality to learning)
        try:
            update_personality("learning_new_idea", 0.3)
        except Exception as e:
            print(f"[message_event] update_personality learning failed: {e}")
        # Outcome-based emotion: new concept triggers curiosity (plan: richer emotion triggers)
        try:
            from app.core.emotions.emotion_engine import trigger_emotion
            trigger_emotion("curiosity", "new_information")
        except Exception as e:
            print(f"[message_event] trigger_emotion failed: {e}")


async def _apply_full_integration(
    message,
    response: str,
    author_entity: str,
    emotional_impact: float,
    dominant: str,
    dominant_intensity: float
) -> None:
    """
    Apply all Phase enhancements for full integration.
    This wires together all the new systems.
    """
    if not FULL_INTEGRATION_AVAILABLE:
        return
    
    # === GOAL-AWARE RESPONSE (Phase 3) ===
    try:
        active_goals = goal_system.get_active_goals()
        for goal in active_goals[:3]:  # Check top 3 goals
            if is_relevant_to(goal, message.content):
                # This conversation might advance the goal
                progress = detect_goal_progress(goal, message.content, response)
                if progress > 0:
                    goal_system.track_progress(goal.id, progress)
                    logger.info(f"🎯 Goal progress: {goal.description[:40]} +{progress:.0%}")
        
        # Check for learning opportunities
        learning_topic = detect_learning_opportunity(message.content)
        if learning_topic:
            # Consider creating a learning goal
            existing = [g for g in active_goals if g.category == "learning"]
            if len(existing) < 3:  # Don't create too many learning goals
                goal_system.create_goal(
                    description=f"Learn more about: {learning_topic}",
                    category="learning",
                    priority=0.5,
                    motivation="This came up in conversation"
                )
                logger.info(f"🎯 Created learning goal: {learning_topic}")
    except Exception as e:
        logger.debug(f"Goal-aware processing failed: {e}")
    
    # === META-AWARENESS INTEGRATION (Phase 7) ===
    try:
        # Check for self-surprise
        recent_predictions = meta_awareness.predictions[-1:] if meta_awareness.predictions else []
        if recent_predictions:
            prediction = recent_predictions[-1]
            if message.content[:50] in prediction.context or prediction.context in message.content[:100]:
                surprise = meta_awareness.check_for_surprise(prediction, response)
                if surprise:
                    logger.info(f"🪞 Self-surprise detected: {surprise[:60]}")
        
        # Generate a prediction for next response
        if len(response) > 50:
            meta_awareness.predict_own_response(
                context=message.content[:100],
                user_message=message.content
            )
    except Exception as e:
        logger.debug(f"Meta-awareness processing failed: {e}")
    
    # === PUBLISH SIGNIFICANT INTERACTION (Phase 1.1) ===
    try:
        if emotional_impact > 0.3:
            awareness_bus.publish_significant_interaction(
                interaction_type="conversation",
                context=f"{message.content[:80]} -> {response[:80]}",
                emotional_impact=emotional_impact,
                person=author_entity
            )
    except Exception as e:
        logger.debug(f"Failed to publish significant interaction: {e}")
    
    # === MEMORY ECHO INTEGRATION (Phase 2) ===
    try:
        topics = [word for word in message.content.lower().split() if len(word) > 4][:5]
        echoes = memory_echo.echo_for_interaction(
            person=author_entity,
            topics=topics,
            current_emotion=dominant
        )
        if echoes:
            logger.debug(f"🧠 {len(echoes)} memory echoes influencing interaction")
    except Exception as e:
        logger.debug(f"Memory echo integration failed: {e}")
    
    # === VALUE CONSULTATION (Phase 5) ===
    try:
        if emotional_impact > 0.5 or dominant_intensity > 60:
            consultation = value_consultation.consult_values(message.content)
            if consultation.get("conflicts"):
                logger.info(f"⚖️ Value tension: {consultation['conflicts'][0]}")
    except Exception as e:
        logger.debug(f"Value consultation failed: {e}")
    
    # === RELATIONSHIP REUNION DETECTION (Phase 4) ===
    try:
        rel = relationship_system.relationships.get(author_entity.lower())
        if rel and rel.days_since_contact() > 2:
            trigger_emotion("love", "reunion")
            stream_of_consciousness.think(
                f"{author_entity} is back after {rel.days_since_contact():.0f} days. I notice warmth.",
                "reflection"
            )
            logger.info(f"💕 Reunion detected with {author_entity}")
    except Exception as e:
        logger.debug(f"Relationship feedback failed: {e}")
