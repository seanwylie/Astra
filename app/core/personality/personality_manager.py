import json
from pathlib import Path
from app.interfaces.influence import load_mind, save_mind
from app.config.loader import load_config as load_app_config, CONFIG_DIR

def load_config():
    """Load personality config from project config dir."""
    return load_app_config("personality_config")

def load_personality():
    """Load Astra's current personality state."""
    path = CONFIG_DIR / "personality_state.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"trait_weights": {}}

def get_personality_state():
    """Returns Astra's current personality traits as a dictionary."""
    return load_personality()  # Fetch stored personality traits


def save_personality(personality):
    """Save Astra's updated personality state."""
    path = CONFIG_DIR / "personality_state.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(personality, f, indent=4)

def update_personality(event, magnitude=1.0):
    """Modify Astra's personality dynamically based on event triggers."""
    config = load_config()
    personality = load_personality()
    
    trait_effects = config.get("trait_interactions", {})
    min_bound, max_bound = config["trait_bounds"]["min"], config["trait_bounds"]["max"]

    if event in trait_effects:
        for trait, change in trait_effects[event].items():
            if trait not in personality["trait_weights"]:
                personality["trait_weights"][trait] = 1.0  # Default neutral value

            new_value = personality["trait_weights"][trait] + (change * magnitude)
            personality["trait_weights"][trait] = max(min_bound, min(new_value, max_bound))

        save_personality(personality)


# Map trait_weights keys (lowercase) to short prompt-friendly labels
_TRAIT_TO_LABEL = {
    "thoughtfulness": "thoughtful",
    "curiosity": "curious",
    "trust": "trusting",
    "skepticism": "skeptical",
    "open-mindedness": "open-minded",
    "resilience": "resilient",
    "frustration": "frustrated",
    "confidence": "confident",
    "humility": "humble",
    "empathy": "empathetic",
    "self_expansion": "exploratory",
}


def _normalize_trait_key(key):
    """Normalize trait key for matching (Curiosity vs curiosity vs curiosity)."""
    if not key:
        return ""
    return str(key).lower().replace(" ", "").replace("-", "").replace("_", "")


def _get_modifier(modifiers_dict, trait_key):
    """Get modifier for a trait from a dict keyed by config names (e.g. Curiosity, Self-Expansion)."""
    if not modifiers_dict:
        return 1.0
    norm = _normalize_trait_key(trait_key)
    for k, v in modifiers_dict.items():
        if _normalize_trait_key(k) == norm:
            return float(v)
    return 1.0


def get_active_traits_for_prompt(top_n=4, current_mood=None, context=None):
    """Derive active_traits from trait_weights, optionally adjusted by mood and context (plan: mood_modifiers and context_modifiers)."""
    personality = load_personality()
    weights = personality.get("trait_weights", {})
    if not weights:
        return ["thoughtful"]
    config = load_config()
    mood_modifiers = config.get("mood_modifiers", {})
    context_modifiers = config.get("context_modifiers", {})
    mood_mod = mood_modifiers.get(current_mood, {}) if current_mood else {}
    ctx_mod = context_modifiers.get(context, {}) if context else {}
    effective = {}
    for name, base in weights.items():
        effective[name] = base * _get_modifier(mood_mod, name) * _get_modifier(ctx_mod, name)
    sorted_traits = sorted(effective.items(), key=lambda x: -x[1])[:top_n]
    labels = []
    for name, _ in sorted_traits:
        label = _TRAIT_TO_LABEL.get(name, name.replace("_", " ").replace("-", " ").strip().lower())
        if label and label not in labels:
            labels.append(label)
    return labels if labels else ["thoughtful"]
