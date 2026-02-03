import time
import logging
from app.core.emotions.emotion_state_manager import (
    load_emotion_state,
    save_emotion_state
)
from app.config.loader import load_config

logger = logging.getLogger(__name__)


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
        logger.warning("Unknown emotion: %s", emotion_name)
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

        logger.debug("Triggered '%s' via '%s' (%+g). New intensity: %.2f", emotion_name, trigger_event, change, new_intensity)
        save_emotion_state(emotion_state)
        
        # Track peak intensities for afterglow/echo (Priority 4.2)
        if new_intensity > 70:
            record_peak_intensity(emotion_name, new_intensity)
        
        # Publish to awareness bus (Phase 1.1)
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_emotion_shift(
                emotion=emotion_name,
                old_intensity=old_intensity,
                new_intensity=new_intensity,
                trigger=trigger_event
            )
        except Exception:
            pass  # Awareness bus may not be available yet

    else:
        logger.debug("No trigger mapping for '%s' in emotion '%s'", trigger_event, emotion_name)


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
            logger.debug("Decayed '%s' (%.2fh): %.2f ➞ %.2f", name, elapsed_hours, current, decayed)

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


# ============================================================
# EMOTIONAL MOMENTUM, AFTERGLOW, AND FLOODING (Priority 4.1-4.3)
# ============================================================

# Track peak intensities for afterglow/echo (emotion -> (peak_intensity, timestamp))
_peak_intensity_history = {}

# Momentum factors - higher = slower to shift away from (0.0 to 1.0)
# These could be moved to emotion_config.json for config-driven tuning
DEFAULT_MOMENTUM_FACTORS = {
    "love": 0.8,      # Very slow to shift
    "grief": 0.9,     # Very slow to shift
    "hate": 0.7,
    "resentment": 0.7,
    "guilt": 0.6,
    "shame": 0.65,
    "curiosity": 0.2,  # Quick to shift
    "hope": 0.4,
    "anger": 0.5,
    "fear": 0.4,
    "joy": 0.3,
    "admiration": 0.4,
    "uncertainty": 0.3,
    "compassion": 0.5,
    "forgiveness": 0.5,
    "confidence": 0.4,
}


def get_emotion_momentum(emotion_name: str) -> float:
    """
    Get the momentum factor for an emotion.
    Higher momentum = more resistant to quick changes.
    
    Emotions like grief and love have high momentum (linger).
    Emotions like curiosity shift easily.
    
    Returns: 0.0 to 1.0 (higher = more momentum)
    """
    config = get_emotion_config()
    emotions_cfg = config.get("emotions", {})
    
    # Check if config has momentum_factor
    if emotion_name in emotions_cfg:
        if "momentum_factor" in emotions_cfg[emotion_name]:
            return emotions_cfg[emotion_name]["momentum_factor"]
    
    # Fall back to defaults
    return DEFAULT_MOMENTUM_FACTORS.get(emotion_name, 0.4)


def calculate_effective_change(emotion_name: str, raw_change: float) -> float:
    """
    Apply momentum to an emotional change.
    
    When an emotion has been dominant for a while, it builds momentum
    and resists quick changes in opposite directions.
    
    Args:
        emotion_name: The emotion being changed
        raw_change: The raw change amount
    
    Returns:
        The effective change after momentum is applied
    """
    emotion_state = load_emotion_state()
    config = get_emotion_config()
    
    entry = emotion_state.get(emotion_name)
    if not isinstance(entry, dict):
        return raw_change
    
    current_intensity = entry.get("intensity", 0)
    last_updated = entry.get("last_updated", time.time())
    
    # Calculate how long this emotion has been significant
    hours_significant = (time.time() - last_updated) / 3600
    
    # Momentum increases with time and intensity
    momentum_factor = get_emotion_momentum(emotion_name)
    
    # If emotion is high and change is negative (reducing it), apply momentum resistance
    if current_intensity > 50 and raw_change < 0:
        # More momentum = more resistance to reduction
        resistance = momentum_factor * min(1.0, current_intensity / 100)
        effective_change = raw_change * (1 - resistance)
        return effective_change
    
    return raw_change


def record_peak_intensity(emotion_name: str, intensity: float) -> None:
    """
    Record a peak intensity for afterglow/echo tracking.
    Called when an emotion reaches a high point.
    """
    global _peak_intensity_history
    
    current_peak = _peak_intensity_history.get(emotion_name, (0, 0))
    
    # Only update if this is a new peak
    if intensity > current_peak[0]:
        _peak_intensity_history[emotion_name] = (intensity, time.time())


def get_emotional_echoes(hours: float = 1.0) -> list:
    """
    Get emotions that hit high intensity recently and still echo.
    
    After intense emotional experiences, there should be lingering effects.
    
    Args:
        hours: How far back to look for peaks
    
    Returns:
        List of (emotion, peak_intensity, hours_ago) for recent peaks
    """
    now = time.time()
    cutoff = now - (hours * 3600)
    
    echoes = []
    for emotion, (peak, timestamp) in _peak_intensity_history.items():
        if timestamp > cutoff and peak > 70:  # Only high-intensity peaks
            hours_ago = (now - timestamp) / 3600
            echoes.append({
                "emotion": emotion,
                "peak_intensity": peak,
                "hours_ago": round(hours_ago, 2)
            })
    
    # Sort by recency
    echoes.sort(key=lambda x: x["hours_ago"])
    return echoes


def has_recent_emotional_echo(emotion_name: str = None, hours: float = 1.0) -> bool:
    """
    Check if there's a lingering emotional echo from a recent peak.
    
    Args:
        emotion_name: Specific emotion to check, or None for any
        hours: How far back to look
    
    Returns:
        True if there's a recent emotional echo
    """
    echoes = get_emotional_echoes(hours)
    
    if emotion_name:
        return any(e["emotion"] == emotion_name for e in echoes)
    
    return len(echoes) > 0


def detect_emotional_flooding(threshold: float = 50.0, min_count: int = 3) -> dict:
    """
    Detect if Astra is emotionally flooded.
    
    Flooding occurs when multiple intense emotions are active simultaneously,
    making it harder to articulate or process any single one.
    
    Args:
        threshold: Intensity above which an emotion is considered "high"
        min_count: Minimum number of high emotions for flooding
    
    Returns:
        Dict with:
        - is_flooded: bool
        - high_emotions: list of (emotion, intensity) above threshold
        - flooding_level: 0.0 to 1.0 (how flooded)
    """
    emotion_state = load_emotion_state()
    
    high_emotions = []
    for emotion, value in emotion_state.items():
        if isinstance(value, dict):
            intensity = value.get("intensity", 0)
        else:
            intensity = value if value is not None else 0
        
        if intensity > threshold:
            high_emotions.append((emotion, intensity))
    
    # Sort by intensity
    high_emotions.sort(key=lambda x: x[1], reverse=True)
    
    is_flooded = len(high_emotions) >= min_count
    
    # Calculate flooding level (0.0 to 1.0)
    # More high emotions and higher intensities = higher flooding
    if not high_emotions:
        flooding_level = 0.0
    else:
        avg_intensity = sum(i for _, i in high_emotions) / len(high_emotions)
        count_factor = min(1.0, len(high_emotions) / 5)  # Max out at 5 emotions
        intensity_factor = min(1.0, avg_intensity / 100)
        flooding_level = (count_factor + intensity_factor) / 2
    
    return {
        "is_flooded": is_flooded,
        "high_emotions": high_emotions,
        "flooding_level": flooding_level,
        "count": len(high_emotions)
    }


def get_emotional_afterglow_context() -> str:
    """
    Generate a prompt-friendly description of emotional afterglow.
    
    Returns a string describing any lingering emotional echoes,
    suitable for including in the response prompt.
    """
    echoes = get_emotional_echoes(hours=2.0)  # Look back 2 hours
    
    if not echoes:
        return ""
    
    # Get the most recent/intense echo
    strongest = max(echoes, key=lambda x: x["peak_intensity"])
    
    if strongest["hours_ago"] < 0.5:
        return f"You recently felt intense {strongest['emotion']}. It still echoes in you."
    else:
        return f"Earlier, you felt strong {strongest['emotion']}. A trace of it lingers."


def update_peak_tracking_on_trigger(emotion_name: str, new_intensity: float) -> None:
    """
    Update peak intensity tracking when an emotion is triggered.
    Called from trigger_emotion.
    """
    if new_intensity > 70:
        record_peak_intensity(emotion_name, new_intensity)


