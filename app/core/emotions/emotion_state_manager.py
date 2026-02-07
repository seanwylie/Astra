# astra_core/emotions/emotion_state_manager.py

import json
import logging
import time
import os
import boto3
from app.config.loader import load_config
from app.core.dinner.dinner_journal import log_if_emotionally_spiking
from app.interfaces.storage_backend import get_backend
# Database sync disabled - only JSON files are backed up to S3

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
EMOTION_STATE_KEY = "emotional_state.json"

s3 = boto3.client("s3")


def get_emotion_config_v2():
    return load_config("emotion_config")


def now():
    return time.time()


def load_emotion_state():
    """Load emotion state using storage backend."""
    backend = get_backend()
    state = backend.load("emotion_state")
    
    if not state:
        logger.debug("No emotion state found. Starting fresh.")
        config = get_emotion_config_v2()
        state = {
            name: {
                "intensity": props["intensity"],
                "last_updated": now()
            }
            for name, props in config["emotions"].items()
        }
        # Save initial state
        save_emotion_state(state)
    
    return state


def save_emotion_state(state):
    """Save emotion state using storage backend."""
    backend = get_backend()
    success = backend.save("emotion_state", state)
    if success:
        logger.debug("Emotion state saved.")
        # Database sync disabled - only JSON files are backed up to S3


def update_emotion(state, emotion, trigger, multiplier=1.0):
    config = get_emotion_config_v2()
    if emotion not in config["emotions"]:
        logger.debug("Unknown emotion: %s", emotion)
        return

    triggers = config["emotions"][emotion].get("triggers", {})
    if trigger not in triggers:
        logger.debug("Trigger %r not defined for emotion %r", trigger, emotion)
        return

    delta = triggers[trigger] * multiplier

    # Normalize emotion state format if it's a raw float
    if isinstance(state.get(emotion), float):
        state[emotion] = {
            "intensity": state[emotion],
            "last_updated": now()
        }

    # Fallback for new emotions not in state
    if emotion not in state:
        state[emotion] = {
            "intensity": config["emotions"][emotion]["intensity"],
            "last_updated": now()
        }

    raw_intensity = state[emotion]["intensity"] + delta
    capped_intensity = min(raw_intensity, config.get("max_intensity", 10000))
    state[emotion]["intensity"] = max(0, capped_intensity)

    logger.debug("Updated '%s' with '%s' (+%s). New intensity: %s", emotion, trigger, delta, state[emotion]["intensity"])
    save_emotion_state(state)

    log_if_emotionally_spiking(state)
