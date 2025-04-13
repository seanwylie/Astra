# astra_core/emotions/emotion_state_manager.py

import json
import time
import os
import boto3
from astra_core.config_loader import load_config
from astra_core.dinner.dinner_journal import log_if_emotionally_spiking




S3_BUCKET = "swylie-astra"
EMOTION_STATE_KEY = "emotional_state.json"

s3 = boto3.client("s3")


def get_emotion_config_v2():
    return load_config("emotion_config")


def now():
    return time.time()


def load_emotion_state():
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=EMOTION_STATE_KEY)
        return json.load(response["Body"])
    except s3.exceptions.NoSuchKey:
        print("📄 No emotion state found. Starting fresh.")
        config = get_emotion_config_v2()
        return {
            name: {
                "intensity": props["intensity"],
                "last_updated": now()
            }
            for name, props in config["emotions"].items()
        }


def save_emotion_state(state):
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=EMOTION_STATE_KEY,
        Body=json.dumps(state, indent=2).encode("utf-8")
    )
    print("✅ Emotion state saved to S3.")


def update_emotion(state, emotion, trigger, multiplier=1.0):
    config = get_emotion_config_v2()
    if emotion not in config["emotions"]:
        print(f"⚠ Unknown emotion: {emotion}")
        return

    triggers = config["emotions"][emotion].get("triggers", {})
    if trigger not in triggers:
        print(f"⚠ Trigger '{trigger}' not defined for emotion '{emotion}'")
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

    print(f"🔁 Updated '{emotion}' with '{trigger}' (+{delta}). New intensity: {state[emotion]['intensity']}")
    save_emotion_state(state)

    log_if_emotionally_spiking(state)
