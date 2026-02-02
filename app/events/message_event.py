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
from discord import Message
from app.core.emotions.emotion_engine import (
    decay_all_emotions, trigger_emotion, get_top_emotions
)
from app.core.dinner.dinner_journal import log_if_ethically_conflicting
from app.core.messaging.message_bus import send_contextual_message
from app.core.knowledge import knowledge_manager
from app.core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from app.interfaces.mind_session import session
from app.core.mood.mood_manager import MoodManager
from app.core.mood.trust_manager import trust_manager
from app.core.personality.personality_manager import get_active_traits_for_prompt, update_personality
from app.config.loader import load_config
from app.services.personality_service import get_current_personality, personality_service

# --- Initialization ---
mood_manager = MoodManager()
mood_config = load_config("mood_config")


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


    # Let commands run first
    await bot.process_commands(message)
    if message.content.startswith(values["command_prefix"]):
        return

    # --- Unknown Term Extraction & Storage ---
    unknown_terms = extract_unknown_terms(message.content)
    for term in unknown_terms:
        definition = lookup_definition(term)
        if definition:
            _store_concept(term, definition)

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
    }

    mind_data = session.load()
    mind_data["emotional_state"] = {**emotions, "dominant": dominant}
    # Per-entity last dominant emotion for prompt continuity (plan: last dominant per user)
    raw = emotions.get(dominant)
    intensity = raw.get("intensity", raw) if isinstance(raw, dict) else (raw if raw is not None else 0.0)
    mind_data.setdefault("last_dominant_emotion_by_entity", {})[author_entity] = {"emotion": dominant, "intensity": intensity}
    session.maybe_save()

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
    for emotion, keywords in trigger_keywords.items():
        if any(k in content_lower for k in keywords):
            trigger_emotion(emotion, "user_prompt")

    # --- Generate and Send Astra's Response ---
    past_convos = knowledge_manager.mind_data.get("past_conversations", [])
    response = send_contextual_message(message.content, internal_state, past_convos)

    for chunk in _chunk_message(response):
        await message.channel.send(chunk, tts=True)
        await asyncio.sleep(1.5)

    # --- Store conversation so past_conversations grows for continuity ---
    mind_data = session.load()
    mind_data.setdefault("past_conversations", [])
    mind_data["past_conversations"].append(f"User: {message.content[:200]}")
    mind_data["past_conversations"].append(f"Astra: {response[:200]}")
    mind_data["past_conversations"] = mind_data["past_conversations"][-100:]
    session.maybe_save()
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


def _store_concept(term: str, definition: str):
    """
    Adds a term/definition pair to Astra’s stored knowledge if it’s new.
    """
    mind = session.load()
    mind.setdefault("stored_knowledge", [])
    formatted = f"📖 **{term}**: {definition}"
    if formatted not in mind["stored_knowledge"]:
        mind["stored_knowledge"].append(formatted)
        session.maybe_save()
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
