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
from astra_core.emotions.emotion_engine import (
    decay_all_emotions, trigger_emotion, get_top_emotions
)
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting
from astra_core.messaging.message_bus import send_contextual_message
from astra_core.knowledge import knowledge_manager
from astra_core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from astra_interfaces.mind_session import session
from astra_core.mood.mood_manager import MoodManager

# --- Initialization ---
mood_manager = MoodManager()


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
    log_if_ethically_conflicting({
        "content": message.content,
        "source": str(message.author)
    })

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

    internal_state = {
        "mood": current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": ["thoughtful"],
        "emotions": emotions
    }

    mind_data = session.load()
    mind_data["emotional_state"] = {**emotions, "dominant": dominant}
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
