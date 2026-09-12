# emotion_service.py

"""
🧪 Emotion Service
------------------
Provides logic for triggering or inspecting Astra's emotional state.

Used primarily by Discord commands to:
- Apply emotion triggers (with custom intensities)
- Report on Astra's dominant feelings and affective description

This service wraps Astra’s emotion config and engine to offer safe, Discord-friendly outputs.

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from app.core.emotions.emotion_state_manager import (
    get_emotion_config_v2,
    load_emotion_state,
    update_emotion
)


def test_emotion_intensity(emotion: str, amount: int = 10) -> str:
    """
    Applies a scaled emotion trigger using a fallback key and returns a status message.

    Args:
        emotion (str): The emotion to test (e.g. "curiosity").
        amount (int): Scaling multiplier for intensity adjustment.

    Returns:
        str: Discord-friendly response message describing the change.
    """
    config = get_emotion_config_v2()

    # Validate emotion
    if emotion not in config["emotions"]:
        return f"⚠️ Unknown emotion: {emotion}"

    # Use first available trigger as fallback key
    triggers = list(config["emotions"][emotion].get("triggers", {}).keys())
    fallback_trigger = triggers[0] if triggers else None

    if not fallback_trigger:
        return f"⚠️ No triggers found for emotion '{emotion}' in config."

    # Apply update
    state = load_emotion_state()
    update_emotion(state, emotion, fallback_trigger, multiplier=amount)

    # Fetch updated value
    updated = state.get(emotion, {})
    intensity = updated.get("intensity", config["emotions"][emotion]["intensity"])

    return (
        f"🧪 Triggered `{emotion}` using `{fallback_trigger}` x{amount}.\n"
        f"New intensity: {intensity:.2f}"
    )


def describe_current_emotions() -> str:
    """
    Returns Astra’s dominant emotion and a narrative interpretation.

    This is used for `!how_are_you` style commands or mood introspection.

    Returns:
        str: A short, human-readable emotional summary.
    """
    from app.core.emotions.emotion_engine import load_emotion_state
    from app.core.messaging.message_bus import (
        describe_emotional_state,
        get_dominant_emotion
    )

    emotions = load_emotion_state()
    if not emotions:
        return "🤷 I'm not sure how I'm feeling right now."

    dominant = get_dominant_emotion(emotions)
    description = describe_emotional_state(emotions)

    return f"💬 I'm currently feeling mostly {dominant}. {description}"
