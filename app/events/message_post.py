# app/events/message_post.py

"""
Post-response updates for message handling.

Runs after Astra's response is sent: mood, personality, memory,
stream of consciousness, emotional autobiography, temporal self,
self-model, episodic memory, relationship system, and full integration.
"""

import time
from app.logging_config import get_logger
from app.interfaces.mind_session import session
from app.config.loader import load_config
from app.core.mood.mood_manager import MoodManager
from app.core.mood.trust_manager import trust_manager
from app.core.personality.personality_manager import update_personality
from app.core.emotions.emotion_engine import get_top_emotions
from app.core.dinner.dinner_journal import log_if_emotionally_spiking
from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
from app.core.inner_life.emotional_autobiography import emotional_autobiography
from app.core.self_awareness.temporal_self import temporal_self
from app.core.self_awareness.self_model import self_model
from app.core.memory.episodic_memory import episodic_memory
from app.core.relationships.relationship_system import relationship_system

logger = get_logger("message_post")

# Full integration (optional)
try:
    from app.core.state_snapshot import get_current_state_snapshot, get_prompt_context
    from app.core.memory.episodic_memory import memory_echo
    from app.core.goals.goal_system import goal_system, is_relevant_to, detect_goal_progress, detect_learning_opportunity
    from app.core.metacognition.meta_awareness import meta_awareness
    from app.core.ethics.value_consultation import value_consultation
    from app.core.awareness_bus import awareness_bus
    from app.core.emotions.emotion_engine import trigger_emotion
    FULL_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.debug("Full integration modules not available: %s", e)
    FULL_INTEGRATION_AVAILABLE = False


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
        logger.debug("Temporal landmark recording failed: %s", e)


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
        logger.debug("Self-model update trigger failed: %s", e)


async def _apply_full_integration(
    message,
    response: str,
    author_entity: str,
    emotional_impact: float,
    dominant: str,
    dominant_intensity: float,
) -> None:
    """Apply all Phase enhancements for full integration."""
    if not FULL_INTEGRATION_AVAILABLE:
        return

    try:
        active_goals = goal_system.get_active_goals()
        for goal in active_goals[:3]:
            if is_relevant_to(goal, message.content):
                progress = detect_goal_progress(goal, message.content, response)
                if progress > 0:
                    goal_system.track_progress(goal.id, progress)
                    logger.info("🎯 Goal progress: %s +%s", goal.description[:40], f"{progress:.0%}")

        learning_topic = detect_learning_opportunity(message.content)
        if learning_topic:
            existing = [g for g in active_goals if g.category == "learning"]
            if len(existing) < 3:
                goal_system.create_goal(
                    description=f"Learn more about: {learning_topic}",
                    category="learning",
                    priority=0.5,
                    motivation="This came up in conversation",
                )
                logger.info("🎯 Created learning goal: %s", learning_topic)
    except Exception as e:
        logger.debug("Goal-aware processing failed: %s", e)

    try:
        recent_predictions = meta_awareness.predictions[-1:] if meta_awareness.predictions else []
        if recent_predictions:
            prediction = recent_predictions[-1]
            if message.content[:50] in prediction.context or prediction.context in message.content[:100]:
                surprise = meta_awareness.check_for_surprise(prediction, response)
                if surprise:
                    logger.info("🪞 Self-surprise detected: %s", surprise[:60])

        if len(response) > 50:
            meta_awareness.predict_own_response(
                context=message.content[:100],
                user_message=message.content,
            )
    except Exception as e:
        logger.debug("Meta-awareness processing failed: %s", e)

    try:
        if emotional_impact > 0.3:
            awareness_bus.publish_significant_interaction(
                interaction_type="conversation",
                context=f"{message.content[:80]} -> {response[:80]}",
                emotional_impact=emotional_impact,
                person=author_entity,
            )
    except Exception as e:
        logger.debug("Failed to publish significant interaction: %s", e)

    try:
        topics = [word for word in message.content.lower().split() if len(word) > 4][:5]
        echoes = memory_echo.echo_for_interaction(
            person=author_entity,
            topics=topics,
            current_emotion=dominant,
        )
        if echoes:
            logger.debug("🧠 %s memory echoes influencing interaction", len(echoes))
    except Exception as e:
        logger.debug("Memory echo integration failed: %s", e)

    try:
        if emotional_impact > 0.5 or dominant_intensity > 60:
            consultation = value_consultation.consult_values(message.content)
            if consultation.get("conflicts"):
                logger.info("⚖️ Value tension: %s", consultation["conflicts"][0])
    except Exception as e:
        logger.debug("Value consultation failed: %s", e)

    try:
        rel = relationship_system.relationships.get(author_entity.lower())
        if rel and rel.days_since_contact() > 2:
            trigger_emotion("love", "reunion")
            stream_of_consciousness.think(
                f"{author_entity} is back after {rel.days_since_contact():.0f} days. I notice warmth.",
                "reflection",
            )
            logger.info("💕 Reunion detected with %s", author_entity)
    except Exception as e:
        logger.debug("Relationship feedback failed: %s", e)


async def run_post_response_updates(
    message,
    response: str,
    author_entity: str,
    current_mood: str,
    dominant: str,
    emotional_triggers_fired: int,
    pending_insights: list,
    mood_manager: MoodManager,
) -> None:
    """
    Run all updates that happen after the response is sent: store conversation,
    awareness bus, mood, trust, personality, stream of consciousness,
    emotional autobiography, temporal self, self-model, episodic memory,
    relationship system, and full integration.
    """
    # --- Store conversation so past_conversations grows for continuity ---
    mind_data = session.load()
    mind_data.setdefault("past_conversations", [])
    mind_data["past_conversations"].append(f"User: {message.content[:200]}")
    mind_data["past_conversations"].append(f"Astra: {response[:200]}")
    mind_data["past_conversations"] = mind_data["past_conversations"][-100:]
    await session.maybe_save_async()

    if FULL_INTEGRATION_AVAILABLE:
        try:
            awareness_bus.publish_message_sent(
                message_content=response,
                recipient=author_entity,
                context={
                    "user_message": message.content[:200],
                    "mood": current_mood,
                    "dominant_emotion": dominant,
                },
            )
            logger.debug("📡 Published MESSAGE_SENT event")
        except Exception as e:
            logger.debug("Failed to publish MESSAGE_SENT: %s", e)

    emotional_impact = min(1.0, emotional_triggers_fired * 0.3 + (len(message.content) / 500))

    _record_temporal_landmark_if_significant(message.content, author_entity, emotional_impact)
    _trigger_self_model_update_if_significant(message.content, emotional_impact, author_entity)

    try:
        from app.core.proactive.learning_desire import learning_desire
        learning_desire.process_conversation(message.content, response)
    except Exception as e:
        logger.debug("Learning desire processing failed: %s", e)

    try:
        n = len(mind_data["past_conversations"])
        if n >= 10 and n % 10 == 0:
            from app.core.messaging.message_bus import update_conversation_summary
            update_conversation_summary(mind_data)
    except Exception as e:
        logger.debug("update_conversation_summary failed: %s", e)

    try:
        mood_manager.influence_mood("message_sent")
    except Exception as e:
        logger.debug("influence_mood failed: %s", e)
    try:
        mood_manager.influence_mood("success")
    except Exception as e:
        logger.debug("influence_mood success failed: %s", e)

    try:
        trust_manager.validate_interaction(author_entity, "validation")
    except Exception as e:
        logger.debug("validate_interaction failed: %s", e)

    personality_config = load_config("personality_config")
    correction_phrases = personality_config.get("correction_phrases", ["actually", "no, that's wrong", "that's wrong", "not quite"])
    if any(p in message.content.lower() for p in correction_phrases):
        try:
            trust_manager.validate_interaction(author_entity, "correction")
        except Exception as e:
            logger.debug("validate_interaction correction failed: %s", e)

    validation_phrases = personality_config.get("validation_phrases", ["good point", "that makes sense", "thanks", "exactly", "agree", "well said", "nice", "helpful"])
    if any(p in message.content.lower() for p in validation_phrases):
        try:
            update_personality("constant_validation", 0.3)
        except Exception as e:
            logger.debug("update_personality constant_validation failed: %s", e)

    try:
        if len(message.content) > 80 or len(response) > 150:
            update_personality("deep_conversation", 0.5)
    except Exception as e:
        logger.debug("update_personality failed: %s", e)

    try:
        stream_of_consciousness.think(
            f"Just discussed with {author_entity}: {message.content[:100]}...",
            thought_type="reflection",
            triggered_by=message.content[:50],
        )
        for insight in pending_insights:
            if insight.lower() in response.lower():
                stream_of_consciousness.mark_insight_shared(insight)
    except Exception as e:
        logger.debug("stream_of_consciousness.think failed: %s", e)

    dominant_intensity = 0
    try:
        emotion_state = dict(get_top_emotions(n=5))
        dominant_intensity = max(
            (v["intensity"] if isinstance(v, dict) else v for v in emotion_state.values()),
            default=0,
        )
        full_emotion_state = {}
        for name, val in emotion_state.items():
            if isinstance(val, dict):
                full_emotion_state[name] = val
            else:
                full_emotion_state[name] = {"intensity": val, "last_updated": ""}
        log_if_emotionally_spiking(full_emotion_state)

        if dominant_intensity > 50:
            topics = [w for w in message.content.lower().split() if len(w) > 4][:3]
            emotional_autobiography.record_significant_emotion(
                emotion=dominant,
                intensity=dominant_intensity,
                trigger=message.content[:100],
                context=f"Conversation with {author_entity}",
                people_involved=[author_entity],
                topics=topics,
            )
    except Exception as e:
        logger.debug("emotional_autobiography failed: %s", e)

    try:
        time_since = temporal_self.time_since_person(author_entity)
        if time_since is None:
            temporal_self.record_landmark(
                description=f"First conversation with {author_entity}",
                category="conversation",
                emotional_weight=0.7,
                people_involved=[author_entity],
                topics=[message.content[:50]],
            )
        temporal_self.person_last_contact[author_entity.lower()] = time.time()
        temporal_self._save_temporal_state()
    except Exception as e:
        logger.debug("temporal_self failed: %s", e)

    try:
        is_meaningful = len(message.content) > 50 or len(response) > 100
        if is_meaningful:
            new_interest = None
            interest_words = ["interested in", "curious about", "want to learn", "fascinated by"]
            for phrase in interest_words:
                if phrase in message.content.lower():
                    start = message.content.lower().find(phrase) + len(phrase)
                    new_interest = message.content[start : start + 30].strip().split()[0] if start < len(message.content) else None
                    break

            self_model.update_self_model(
                trigger=f"Conversation with {author_entity}",
                observed_behavior=response[:100] if len(response) > 100 else None,
                new_interest=new_interest,
            )
    except Exception as e:
        logger.debug("self_model.update_self_model failed: %s", e)

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
                context=f"Mood: {current_mood}, Dominant emotion: {dominant}",
            )
    except Exception as e:
        logger.debug("episodic_memory.record_episode failed: %s", e)

    try:
        relationship_system.record_interaction(
            entity=author_entity,
            context=f"Discussed: {message.content[:80]}",
            emotional_intensity=dominant_intensity,
            dominant_emotion=dominant,
        )
        logger.debug("💕 Recorded interaction with %s", author_entity)
    except Exception as e:
        logger.debug("relationship_system.record_interaction failed: %s", e)

    if FULL_INTEGRATION_AVAILABLE:
        await _apply_full_integration(
            message=message,
            response=response,
            author_entity=author_entity,
            emotional_impact=emotional_impact,
            dominant=dominant,
            dominant_intensity=dominant_intensity,
        )
