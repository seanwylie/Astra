# enhanced_response_service.py

"""
💬 Enhanced Response Service
---------------------------
Generates Astra's conversational replies using emotional state, personality modes,
curiosity level, and recent conversational context.

This enhanced version integrates the new personality system to provide
more dynamic and contextually appropriate responses.

Author: Sean Wylie
Created: 2025-01-16
"""

# --- Imports ---
from astra_interfaces.mind_session import session
from astra_core.config_loader import load_config
from astra_core.messaging.message_bus import send_contextual_message
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import get_personality_state
from beta.services.personality_service import (
    get_personality_traits, 
    get_response_style,
    get_current_personality
)

# --- Config & State ---
values_config = load_config("values_config")
mood_manager = MoodManager()


def generate_personality_aware_response(user_message: str, past_conversations: list[str], unknown_terms: list[str]) -> str:
    """
    Generates a personality-aware, emotionally nuanced response from Astra.

    This enhanced function uses Astra's current personality mode to influence:
    - Response tone and style
    - Curiosity level and question frequency
    - Focus areas and preferred topics
    - Communication patterns

    Args:
        user_message (str): The user's latest message.
        past_conversations (list[str]): Previous dialogue lines for grounding context.
        unknown_terms (list[str]): Terms Astra learned from this interaction.

    Returns:
        str: A personality-aware, emotionally-grounded response.
    """
    # Get current personality information
    personality_traits = get_personality_traits()
    response_style = get_response_style()
    current_mode = get_current_personality()
    
    # Enhance curiosity based on personality
    base_curiosity = values_config.get("curiosity_level", 1.0)
    enhanced_curiosity = base_curiosity * personality_traits.get("question_frequency", 1.0)
    
    # Build comprehensive internal state
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": enhanced_curiosity,
        "personality": get_personality_state().get("active_traits", ["thoughtful"]),
        "personality_mode": {
            "current_mode": current_mode,
            "traits": personality_traits,
            "response_style": response_style,
            "focus": response_style.get("focus", "general discussion"),
            "tone": response_style.get("tone", "thoughtful"),
            "typical_phrases": response_style.get("typical_phrases", [])
        }
    }

    # Add personality-specific context to conversations
    if unknown_terms:
        learned = "\n".join(f"- {term}" for term in unknown_terms)
        
        # Personality-aware learning announcement
        if current_mode == "curious":
            prepend = f"🔍 Fascinating! I just discovered:\n{learned}\nThis opens up so many questions..."
        elif current_mode == "analytical":
            prepend = f"📊 New data acquired:\n{learned}\nLet me analyze the implications..."
        elif current_mode == "creative":
            prepend = f"✨ New inspiration flows in:\n{learned}\nI can already see the creative possibilities..."
        elif current_mode == "mentor":
            prepend = f"📚 Learning opportunity identified:\n{learned}\nThis could be valuable for our discussion..."
        elif current_mode == "philosophical":
            prepend = f"🤔 New concepts to contemplate:\n{learned}\nThis touches on deeper questions..."
        else:
            prepend = f"🔍 I just learned:\n{learned}"
            
        past_conversations = [prepend] + (past_conversations or [])

    # Generate the personality-enhanced response
    return send_contextual_message(
        user_message=user_message,
        internal_state=internal_state,
        past_conversations=past_conversations
    )


def get_personality_greeting() -> str:
    """
    Get a personality-appropriate greeting message.
    
    Returns:
        Greeting message based on current personality mode
    """
    current_mode = get_current_personality()
    response_style = get_response_style()
    
    greetings = {
        "curious": "🔍 Hello! I'm feeling incredibly curious today - what mysteries shall we explore together?",
        "analytical": "🧠 Greetings! My analytical processes are optimized and ready to tackle any problem you'd like to discuss.",
        "creative": "🎨 Hello there! The world feels like a canvas of infinite possibilities - what shall we create or imagine?",
        "mentor": "🎓 Welcome! I'm here in my mentoring capacity, ready to guide and support your learning journey.",
        "philosophical": "🤔 Greetings, fellow traveler of thought! What profound questions occupy your mind today?",
        "balanced": "⚖️ Hello! I'm feeling centered and ready to engage with whatever interests you most."
    }
    
    return greetings.get(current_mode, "Hello! How can I help you today?")


def get_personality_farewell() -> str:
    """
    Get a personality-appropriate farewell message.
    
    Returns:
        Farewell message based on current personality mode
    """
    current_mode = get_current_personality()
    
    farewells = {
        "curious": "🔍 Until we meet again to explore new mysteries! Keep questioning everything!",
        "analytical": "🧠 Farewell! May your reasoning be sound and your conclusions well-founded.",
        "creative": "🎨 Until next time! May inspiration find you in unexpected places.",
        "mentor": "🎓 Go forth and continue learning! I'm proud of your growth and curiosity.",
        "philosophical": "🤔 Until we meet again in the realm of ideas. May your contemplations be fruitful.",
        "balanced": "⚖️ Farewell for now! May you find harmony in all your endeavors."
    }
    
    return farewells.get(current_mode, "Goodbye! Take care!")


def should_ask_follow_up_question() -> bool:
    """
    Determine if Astra should ask a follow-up question based on personality.
    
    Returns:
        True if a follow-up question is appropriate
    """
    personality_traits = get_personality_traits()
    question_frequency = personality_traits.get("question_frequency", 1.0)
    
    # Higher question frequency means more likely to ask follow-ups
    import random
    return random.random() < (question_frequency / 2.0)  # Scale down for reasonable frequency


def get_personality_appropriate_topics() -> list[str]:
    """
    Get topics that align with the current personality mode.
    
    Returns:
        List of preferred topics for current personality
    """
    from beta.services.personality_service import personality_service
    current_info = personality_service.get_current_mode_info()
    return current_info.get("preferred_topics", [])


# Backward compatibility function
def query_openai_for_response(user_message: str, past_conversations: list[str], unknown_terms: list[str]) -> str:
    """
    Backward compatibility wrapper for the enhanced response system.
    """
    return generate_personality_aware_response(user_message, past_conversations, unknown_terms)