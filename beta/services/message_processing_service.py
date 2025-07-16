# message_processing_service.py

"""
📨 Message Processing Service
-----------------------------
Handles the core message processing logic that was previously in discord_astra.py.

This includes:
- Emotion triggering based on message content
- Unknown term detection and storage
- Response generation with emotional context
- Message chunking for Discord TTS

Author: Sean Wylie
Created: 2025-01-16
"""

import re
import asyncio
from typing import List, Dict, Any, Tuple

# Core Astra imports
from astra_interfaces.mind_session import session
from astra_core.emotions.emotion_engine import (
    get_top_emotions, 
    trigger_emotion, 
    decay_all_emotions,
    load_emotion_state
)
from astra_core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from astra_core.knowledge import knowledge_manager
from astra_core.mood.mood_manager import MoodManager
from astra_core.messaging.message_bus import send_contextual_message
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting
from astra_core.personality.personality_manager import get_personality_state

# Initialize managers
mood_manager = MoodManager()


def store_concept(term: str, definition: str) -> None:
    """
    Add a new concept and its definition to stored knowledge.
    
    Args:
        term: The term to store
        definition: The definition of the term
    """
    mind_data = session.load()
    mind_data.setdefault("stored_knowledge", [])

    formatted_entry = f"📖 **{term}**: {definition}"

    if formatted_entry not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(formatted_entry)
        session.maybe_save()
        print(f"✅ Stored new concept: {formatted_entry}")
    else:
        print(f"⚠ Concept '{term}' already exists in memory.")


def process_unknown_terms(user_message: str) -> List[str]:
    """
    Extract and store unknown terms from user message.
    
    Args:
        user_message: The user's message content
        
    Returns:
        List of newly learned terms
    """
    unknown_terms = extract_unknown_terms(user_message)
    learned_terms = []
    
    for term in unknown_terms:
        definition = lookup_definition(term)
        if definition:
            store_concept(term, definition)
            learned_terms.append(term)
    
    return learned_terms


def trigger_emotions_from_message(user_message: str) -> Dict[str, float]:
    """
    Analyze message content and trigger appropriate emotions.
    
    Args:
        user_message: The user's message content
        
    Returns:
        Dictionary of current emotional state
    """
    # Apply decay first
    decay_all_emotions()
    
    # Trigger new emotions based on user input
    user_message_lower = user_message.lower()
    trigger_map = {
        "love": ["love", "friend", "hug", "kind"],
        "anger": ["hate", "angry", "frustrated", "stupid"],
        "curiosity": ["why", "how", "what", "wonder"],
        "grief": ["loss", "miss", "sad", "gone"],
        "admiration": ["amazing", "beautiful", "proud", "genius"],
        "hope": ["hope", "someday", "future"],
        "uncertainty": ["maybe", "not sure", "unsure", "confused"],
    }

    for emotion, keywords in trigger_map.items():
        if any(kw in user_message_lower for kw in keywords):
            trigger_emotion(emotion, "user_prompt")

    # Get updated emotional state
    top_emotions = get_top_emotions(n=3)
    dominant_emotion, _ = top_emotions[0] if top_emotions else ("neutral", 0.0)
    emotions = dict(top_emotions) if top_emotions else {}

    # Save emotional snapshot into mind file
    mind_data = session.load()
    mind_data["emotional_state"] = emotions
    mind_data["emotional_state"]["dominant"] = dominant_emotion
    session.maybe_save()
    
    return emotions


def generate_contextual_response(
    user_message: str, 
    emotions: Dict[str, float], 
    learned_terms: List[str]
) -> str:
    """
    Generate Astra's response using emotional context and learned terms.
    
    Args:
        user_message: The user's message
        emotions: Current emotional state
        learned_terms: Terms learned from this interaction
        
    Returns:
        Astra's contextual response
    """
    # Get past conversations for context
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])
    
    # Build internal state
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": 1.0,  # TODO: Make dynamic
        "personality": get_personality_state().get("active_traits", ["thoughtful"]),
        "emotions": emotions
    }
    
    # If new terms were learned, prepend them to conversation context
    if learned_terms:
        new_knowledge = "\n".join(f"- {term}" for term in learned_terms)
        past_conversations = [f"🔍 Astra just learned:\n{new_knowledge}"] + (past_conversations or [])
    
    return send_contextual_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )


def chunk_response_for_discord(response: str, chunk_size: int = 200) -> List[str]:
    """
    Split response into logical chunks for Discord TTS.
    
    Args:
        response: The full response text
        chunk_size: Maximum characters per chunk
        
    Returns:
        List of response chunks
    """
    response_chunks = []
    sentences = re.split(r'(?<=[.!?]) ', response)

    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > chunk_size:
            if current_chunk.strip():
                response_chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence

    if current_chunk.strip():
        response_chunks.append(current_chunk.strip())
    
    return response_chunks


async def process_user_message(message_content: str, author_info: str) -> Tuple[List[str], Dict[str, Any]]:
    """
    Complete message processing pipeline.
    
    Args:
        message_content: The user's message content
        author_info: Information about the message author
        
    Returns:
        Tuple of (response_chunks, processing_metadata)
    """
    # Log potential ethical conflicts
    log_if_ethically_conflicting({
        "content": message_content,
        "source": author_info
    })
    
    # Process unknown terms
    learned_terms = process_unknown_terms(message_content)
    
    # Trigger emotions based on message content
    emotions = trigger_emotions_from_message(message_content)
    
    # Generate contextual response
    response = generate_contextual_response(message_content, emotions, learned_terms)
    
    # Chunk response for Discord
    response_chunks = chunk_response_for_discord(response)
    
    # Prepare metadata
    metadata = {
        "learned_terms": learned_terms,
        "emotions": emotions,
        "dominant_emotion": emotions.get("dominant", "neutral") if emotions else "neutral",
        "chunk_count": len(response_chunks)
    }
    
    return response_chunks, metadata


async def send_chunked_response(send_func, response_chunks: List[str], use_tts: bool = True, delay: float = 1.5):
    """
    Send response chunks with appropriate delays.
    
    Args:
        send_func: Discord send function (e.g., message.channel.send)
        response_chunks: List of response chunks
        use_tts: Whether to use text-to-speech
        delay: Delay between chunks in seconds
    """
    for chunk in response_chunks:
        if chunk.strip():
            await send_func(chunk, tts=use_tts)
            if len(response_chunks) > 1:  # Only delay if multiple chunks
                await asyncio.sleep(delay)
        else:
            print("[message_processing_service] ⚠ Skipping empty message chunk.")