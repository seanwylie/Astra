import time
from astra_core.emotions.emotion_state_manager import (
    load_emotion_state,
    save_emotion_state
)
from astra_core.config_loader import load_config

def get_emotion_config():
    return load_config("emotion_config")

def trigger_emotion(emotion_name, trigger_event):
    """Apply a trigger to an emotion and update its intensity accordingly."""
    emotion_state = load_emotion_state()
    config = get_emotion_config()
    emotions = config.get("emotions", {})

    if emotion_name not in emotions:
        print(f"⚠️ Unknown emotion: {emotion_name}")
        return

    emotion = emotions[emotion_name]
    trigger_map = emotion.get("triggers", {})
    change = trigger_map.get(trigger_event)

    if change is not None:
        # Extract or fallback to config-defined intensity
        old_entry = emotion_state.get(emotion_name)
        old_intensity = old_entry["intensity"] if isinstance(old_entry, dict) else old_entry

        new_intensity = max(0, old_intensity + change)

        # Update and persist
        emotion_state[emotion_name] = {
            "intensity": new_intensity,
            "last_updated": time.time()
        }

        print(f"[emotion_engine] 🔁 Triggered '{emotion_name}' via '{trigger_event}' ({change:+}). New intensity: {new_intensity:.2f}")
        save_emotion_state(emotion_state)

    else:
        print(f"[emotion_engine] ⚠️ No trigger mapping for '{trigger_event}' in emotion '{emotion_name}'")


def decay_all_emotions():
    """Apply decay to all emotions over time."""
    emotion_state = load_emotion_state()
    config = get_emotion_config()
    emotions = config.get("emotions", {})

    for name, props in emotions.items():
        value = emotion_state.get(name, props["intensity"])

        # If structured, extract intensity
        if isinstance(value, dict) and "intensity" in value:
            current = value["intensity"]
        else:
            current = value

        decay_rate = props.get("decay_rate", 0.05)
        decayed = max(0, current * (1 - decay_rate))

        # Repack into structured format
        emotion_state[name] = {
            "intensity": decayed,
            "last_updated": time.time()
        }

        print(f"[emotion_engine] 🧪 Decayed '{name}': {current:.2f} ➞ {decayed:.2f}")


    save_emotion_state(emotion_state)


def get_top_emotions(n=3):
    """Return the top N emotions by intensity."""
    emotion_state = load_emotion_state()

    # Flatten intensities if values are nested
    flattened = {
        name: (props["intensity"] if isinstance(props, dict) and "intensity" in props else props)
        for name, props in emotion_state.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    return sorted_emotions[:n]


def get_emotion_intensity(emotion_name):
    """Returns the current intensity of a given emotion."""
    state = load_emotion_state()
    return state.get(emotion_name, 0)


def get_dominant_emotion(emotions: dict) -> str:
    if not emotions:
        return "curiosity"

    # Extract and clamp intensities
    flattened = {
        name: min(
            value["intensity"] if isinstance(value, dict) else value,
            100  # Clamp at 100 for dominance logic
        )
        for name, value in emotions.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    top_emotion, top_score = sorted_emotions[0]

    # Special override for obsession
    if "obsession" in flattened and flattened["obsession"] > 90:
        return "obsession"

    # Try resolving emotional conflicts
    opposites = {
        "hate": "love",
        "anger": "compassion",
        "grief": "hope",
        "resentment": "forgiveness",
        "uncertainty": "confidence"
    }

    for neg, pos in opposites.items():
        if neg in flattened and pos in flattened:
            if flattened[pos] > flattened[neg] + 2:
                return pos

    return top_emotion


