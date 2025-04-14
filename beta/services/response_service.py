# response_service.py

"""
💬 Response Service
-------------------
Generates Astra's conversational replies using emotional state, personality traits,
curiosity level, and recent conversational context.

This wrapper ensures Astra's responses are emotionally grounded and self-consistent,
while keeping logic decoupled from Discord and UI concerns.

Author: Sean Wylie
Created: 2025-04-15
"""

# --- Imports ---
from astra_interfaces.mind_session import session
from astra_core.config_loader import load_config
from astra_core.messaging.message_bus import send_contextual_message
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import get_personality_state

# --- Config & State ---
values_config = load_config("values_config")
mood_manager = MoodManager()


# --- Public API ---

def query_openai_for_response(user_message: str, past_conversations: list[str], unknown_terms: list[str]) -> str:
    """
    Generates a context-aware, emotionally nuanced response from Astra.

    This is the primary entry point for generating Astra's replies using:
    - Her current mood
    - Curiosity level
    - Personality traits
    - Any newly acquired terms
    - Historical conversation context

    Args:
        user_message (str): The user's latest message.
        past_conversations (list[str]): Previous dialogue lines for grounding context.
        unknown_terms (list[str]): Terms Astra learned from this interaction.

    Returns:
        str: A thoughtful, emotionally-aware response.
    """
    # Build Astra’s current internal state
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }

    # If new terms were discovered, prepend them to the conversation history
    if unknown_terms:
        learned = "\n".join(f"- {term}" for term in unknown_terms)
        prepend = f"🔍 Astra just learned:\n{learned}"
        past_conversations = [prepend] + (past_conversations or [])

    # Generate the final response using the message bus
    return send_contextual_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )
