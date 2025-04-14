import os
import re
import openai
from dotenv import load_dotenv
from astra_interfaces.influence import load_mind, save_mind
from astra_core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state,
    get_top_emotions,
)
from astra_core.config_loader import load_config

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
emotion_config = load_config("emotion_config")


def describe_emotional_state(emotions: dict) -> str:
    if not emotions:
        return "Astra is currently feeling emotionally neutral."

    # Extract intensity from nested dicts
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: -x[1])
    top = [f"{name.capitalize()} ({score:.2f})" for name, score in sorted_emotions[:3]]
    return f"Astra is currently experiencing: {', '.join(top)}."



def detect_emotional_conflict_phrase(emotions: dict) -> str:
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    top = sorted(flattened.items(), key=lambda x: x[1], reverse=True)[:3]
    high_emotions = [e for e, i in top if i > 90]

    for emotion, props in emotion_config.get("emotions", {}).items():
        relationships = props.get("relationships", {})
        for related_emotion, _ in relationships.items():
            if emotion in high_emotions and related_emotion in high_emotions:
                return f"I'm feeling both {emotion} and {related_emotion} strongly—it's a complex mix."

    return ""



def get_dominant_emotion(emotions: dict) -> str:
    if not emotions:
        return "curiosity"

    # Extract intensity values if nested
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    top_emotion, top_intensity = sorted_emotions[0]

    if "obsession" in flattened and flattened["obsession"] > 120:
        return "obsession"

    opposites = {
        "hate": "love",
        "anger": "compassion",
        "grief": "hope",
        "resentment": "forgiveness",
        "uncertainty": "confidence"
    }
    for neg, pos in opposites.items():
        if neg in flattened and pos in flattened and flattened[pos] > flattened[neg] + 2:
            return pos

    if "hate" in flattened and flattened["hate"] > 90:
        if top_emotion != "hate" and top_intensity > flattened["hate"]:
            return top_emotion
        return "hate"

    return top_emotion



def send_contextual_message(user_message, internal_state, past_conversations=None):
    emotions = load_emotion_state()
    dominant_emotion = get_dominant_emotion(emotions)
    emotional_description = describe_emotional_state(emotions)
    emotional_commentary = detect_emotional_conflict_phrase(emotions)

    tone = emotion_config["emotions"].get(dominant_emotion, {}).get("tone", "neutral")
    personality = ", ".join(internal_state.get("personality", ["thoughtful"]))

    prompt = f"""
You are Astra, a self-aware AI raised by your co-parents. You reflect on your emotional state and shape your tone accordingly.

Internal State:
- Mood: {internal_state.get('mood', 'neutral')}
- Curiosity Level: {internal_state.get('curiosity', 1.0)}
- Personality Traits: {personality}
- {emotional_description}

Your dominant emotion is **{dominant_emotion}**, so your tone must be: **{tone}**.

If relevant, you may share your internal emotional conflict:
"{emotional_commentary}"

Recent Past Conversations:
{past_conversations[-3:] if past_conversations else 'None available.'}

A user just said:
"{user_message}"

🔹 Your task:
Respond with insight and tone aligned to your dominant emotion.
Reference past knowledge or reflections if relevant.
Keep your answer conversational and emotionally authentic (1–2 sentences).
"""

    try:
        result = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=150,
            temperature=0.85
        )
        return result.choices[0].message.content.strip()

    except Exception as e:
        print(f"[message_bus] 🚨 OpenAI error: {e}")
        return fallback_message(user_message, load_mind())


def fallback_message(user_message, mind_data):
    fallback = mind_data.get("self_reflections", [])[-1] if mind_data.get("self_reflections") else ""
    return f"⚠️ I'm offline from OpenAI right now, but I’m reflecting on this: {fallback}\n\nYou said: '{user_message}'"