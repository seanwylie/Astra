import time
from app.core.emotions.emotion_state_manager import (
    load_emotion_state,
    save_emotion_state
)
from app.config.loader import load_config

def get_emotion_config():
    return load_config("emotion_config")


# Scale factor for relationship propagation (plan: use emotion relationships)
RELATIONSHIP_PROPAGATION_SCALE = 0.3


def _apply_relationship_propagation(emotion_state, emotion_name, config):
    """Apply small deltas to related emotions from config relationships (plan: emotion relationships)."""
    emotions_cfg = config.get("emotions", {})
    if emotion_name not in emotions_cfg:
        return
    relationships = emotions_cfg[emotion_name].get("relationships", {})
    if not relationships:
        return
    now = time.time()
    max_intensity = config.get("max_intensity", 10000)
    for related_name, delta in relationships.items():
        if related_name not in emotions_cfg:
            continue
        scaled_delta = delta * RELATIONSHIP_PROPAGATION_SCALE
        entry = emotion_state.get(related_name)
        if isinstance(entry, dict):
            current = entry.get("intensity", emotions_cfg[related_name]["intensity"])
        else:
            current = entry if entry is not None else emotions_cfg[related_name]["intensity"]
        new_val = max(0, min(max_intensity, current + scaled_delta))
        emotion_state[related_name] = {
            "intensity": new_val,
            "last_updated": entry.get("last_updated", now) if isinstance(entry, dict) else now
        }
        emotion_state[related_name]["last_updated"] = now


# In-memory log for rate limiting: (emotion_name, trigger_event) -> [(timestamp, delta), ...] (plan: rate limiting)
_trigger_log = []


def _apply_trigger_rate_limit(emotion_name, trigger_event, change, config):
    """Cap change by rate limit for (emotion, trigger) in window (plan: rate limiting). Returns effective change."""
    rate_cfg = config.get("trigger_rate_limit") or {}
    window_seconds = rate_cfg.get("window_seconds", 3600)
    max_per_trigger = rate_cfg.get("max_delta_per_trigger", {})
    cap = max_per_trigger.get(trigger_event)
    if cap is None or change <= 0:
        return change
    now = time.time()
    cutoff = now - window_seconds
    global _trigger_log
    _trigger_log = [(e, t, ts, d) for (e, t, ts, d) in _trigger_log if ts >= cutoff]
    total_in_window = sum(d for (e, t, ts, d) in _trigger_log if e == emotion_name and t == trigger_event)
    allowed = max(0, cap - total_in_window)
    effective = min(change, allowed) if allowed >= 0 else 0
    if effective > 0:
        _trigger_log.append((emotion_name, trigger_event, now, effective))
    return effective


def trigger_emotion(emotion_name, trigger_event):
    """Apply a trigger to an emotion and update its intensity accordingly (with optional rate limiting)."""
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
        change = _apply_trigger_rate_limit(emotion_name, trigger_event, change, config)
        if change == 0:
            return
        # Extract or fallback to config-defined intensity
        old_entry = emotion_state.get(emotion_name)
        old_intensity = old_entry["intensity"] if isinstance(old_entry, dict) else old_entry

        new_intensity = max(0, old_intensity + change)

        # Update and persist
        emotion_state[emotion_name] = {
            "intensity": new_intensity,
            "last_updated": time.time()
        }

        # Plan: emotion relationships — propagate small delta to related emotions
        _apply_relationship_propagation(emotion_state, emotion_name, config)

        print(f"[emotion_engine] 🔁 Triggered '{emotion_name}' via '{trigger_event}' ({change:+}). New intensity: {new_intensity:.2f}")
        save_emotion_state(emotion_state)

    else:
        print(f"[emotion_engine] ⚠️ No trigger mapping for '{trigger_event}' in emotion '{emotion_name}'")


# Hours per "decay tick" for time-based decay (plan: time-based decay using last_updated)
DECAY_TICK_HOURS = 1.0


def decay_all_emotions():
    """Apply time-based decay to all emotions using last_updated (plan: time-based decay)."""
    emotion_state = load_emotion_state()
    config = get_emotion_config()
    emotions = config.get("emotions", {})
    now = time.time()

    for name, props in emotions.items():
        entry = emotion_state.get(name)
        if isinstance(entry, dict):
            current = entry.get("intensity", props["intensity"])
            last_updated = entry.get("last_updated", now)
        else:
            current = entry if entry is not None else props["intensity"]
            last_updated = now

        decay_rate = props.get("decay_rate", 0.05)
        elapsed_hours = max(0.0, (now - last_updated) / 3600.0)
        # Exponential decay: one tick per hour
        decay_factor = (1.0 - decay_rate) ** elapsed_hours
        decayed = max(0.0, current * decay_factor)

        emotion_state[name] = {
            "intensity": decayed,
            "last_updated": now
        }

        if elapsed_hours > 0.01:
            print(f"[emotion_engine] 🧪 Decayed '{name}' ({elapsed_hours:.2f}h): {current:.2f} ➞ {decayed:.2f}")

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


