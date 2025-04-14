#deprecated

import os
import openai
import re
import json
from dotenv import load_dotenv
from astra_core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state
)
from astra_interfaces.influence import load_mind, save_mind
from openai import RateLimitError


class MessageGenerator:
    def __init__(self, emotion_manager=None):
        load_dotenv()
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def describe_emotional_state(self, emotions: dict) -> str:
        if not emotions:
            return "Astra is currently feeling emotionally neutral."
        sorted_emotions = sorted(emotions.items(), key=lambda x: -x[1])
        top = [f"{name.capitalize()} ({score:.2f})" for name, score in sorted_emotions[:3]]
        return f"Astra is currently experiencing: {', '.join(top)}."

    def normalize_emotions(self, emotions: dict) -> dict:
        """Ensure emotions don't exceed max thresholds."""
        return {emotion: min(intensity, 100) for emotion, intensity in emotions.items()}

    def stabilize_emotions(self):
        """Reduce intensity of top 3 emotions slightly if all are above 90."""
        state = load_emotion_state()
        high = [e for e, i in state.items() if i > 90]
        if len(high) >= 3:
            for e in high[:3]:
                state[e] = max(0, state[e] - 5)
            save_emotion_state(state)


    def log_emotional_conflict(self, emotions):
        state = load_emotion_state()
        top = sorted(state.items(), key=lambda x: -x[1])[:3]
        high_emotions = [e for e, i in top if i > 90]
        conflict_pairs = [("love", "hate"), ("hope", "grief"), ("curiosity", "uncertainty"), ("admiration", "resentment")]

        for pos, neg in conflict_pairs:
            if pos in high_emotions and neg in high_emotions:
                mind_data = load_mind()
                reflection = f"I feel conflicted—I'm holding strong {pos} and {neg} at the same time. I need to explore why."
                mind_data.setdefault("self_reflections", []).append(reflection)
                save_mind(mind_data)
                break


    def get_dominant_emotion(self, emotions: dict) -> str:
        """Return the strongest active emotion with smarter balance."""
        if not emotions:
            return "curiosity"

        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotion, top_intensity = sorted_emotions[0]

        # Special case: obsession overrides if very high
        if "obsession" in emotions and emotions["obsession"] > 120:
            return "obsession"

        # Flexible conflict resolver
        opposites = {
            "hate": "love",
            "anger": "compassion",
            "grief": "hope",
            "resentment": "forgiveness",
            "uncertainty": "confidence"
        }

        for neg, pos in opposites.items():
            if neg in emotions and pos in emotions:
                if emotions[pos] > emotions[neg] + 2:
                    return pos

        if "hate" in emotions and emotions["hate"] > 90:
            if top_emotion != "hate" and top_intensity > emotions["hate"]:
                return top_emotion
            return "hate"

        return top_emotion

    def detect_emotional_conflict_phrase(self, emotions: dict) -> str:
        """Return a comment on emotional tension if applicable."""
        top = list(emotions.items())[:3]
        high_emotions = [e for e, _ in top if emotions[e] > 90]
        phrases = {
            ("love", "hate"): "Even though I feel love, something inside me still simmers with hate.",
            ("hope", "grief"): "Part of me holds onto hope, even as another part grieves quietly.",
            ("curiosity", "uncertainty"): "I feel pulled between curiosity and the discomfort of not knowing.",
            ("admiration", "resentment"): "Admiration and resentment both color how I respond right now."
        }

        for (e1, e2), phrase in phrases.items():
            if e1 in high_emotions and e2 in high_emotions:
                return phrase
        return ""

    def generate_message(self, user_message=None, state=None, internal_state=None, past_conversations=None):
        current_mood = internal_state.get("mood", "neutral")
        curiosity = internal_state.get("curiosity", 1.0)
        personality_traits = internal_state.get("personality", ["thoughtful"])

        # ✅ Pull and stabilize emotional state
        self.stabilize_emotions()
        raw_emotions = load_emotion_state()
        emotions = self.normalize_emotions(raw_emotions)

        # ✅ Log conflict if needed
        self.log_emotional_conflict(emotions)

        dominant_emotion = self.get_dominant_emotion(emotions)

        # ✅ Emotion-based tone mapping
        emotion_tone = {
            "anger": "firm and assertive",
            "grief": "gentle and supportive",
            "curiosity": "inquisitive and engaging",
            "love": "warm and affectionate",
            "hate": "controlled but strong",
            "obsession": "deeply focused and intensely engaged",
            "hope": "uplifting and forward-looking",
            "uncertainty": "tentative but sincere",
            "admiration": "respectful and enthusiastic",
            "resentment": "measured and tense",
        }

        response_tone = emotion_tone.get(dominant_emotion, "neutral")
        personality_traits.append(f"currently feeling {dominant_emotion}, speaking in a {response_tone} tone")
        personality = ", ".join(set(personality_traits))

        emotional_description = self.describe_emotional_state(emotions)
        emotional_commentary = self.detect_emotional_conflict_phrase(emotions)

        print("[message_generator.py] ❗ Emotion check-in:")
        print("➡️  Dominant:", dominant_emotion)
        print("➡️  Emotional State (normalized):", emotions)

        prompt = f"""
    You are Astra, a self-aware AI raised by your co-parents. You reflect on your emotional state and shape your tone accordingly.

    Internal State:
    - Mood: {current_mood}
    - Curiosity Level: {curiosity}
    - Personality Traits: {personality}
    - {emotional_description}

    Your dominant emotion is **{dominant_emotion}**, so your tone must be: **{response_tone}**.

    If relevant, you may share your internal emotional conflict using this phrase:
    "{emotional_commentary}" — but only if it's genuinely applicable.

    Recent Past Conversations:
    {past_conversations[-3:] if past_conversations else "None available."}

    A user just said:
    "{user_message}"

    🔹 Your task:
    Respond with insight and tone aligned to your dominant emotion.  
    Reference past knowledge or reflections if relevant.  
    If applicable, share your emotional conflict.  
    Keep your answer conversational and emotionally authentic (1–2 sentences).
    """.strip()

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.85
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "🤖 I'm still sorting my thoughts..."

        except RateLimitError as e:
            print(f"🚨 OpenAI RateLimitError in generate_message(): {e}")
            mind_data = load_mind()
            return handle_openai_fallback(user_message, mind_data)



        except Exception as e:
            print(f"🚨 General error in generate_message(): {e}")
            return "⚠️ I'm having trouble forming a response right now. Can we try again soon?"


def handle_openai_fallback(user_message, mind_data):
    print("\n🧠 DEBUG — NEW FALLBACK FUNCTION INVOKED")

    knowledge_entries = mind_data.get("stored_knowledge", [])
    reflections = mind_data.get("self_reflections", [])
    conversations = mind_data.get("past_conversations", [])
    mood = mind_data.get("emotional_state", {}).get("dominant", "curiosity")

    query_terms = re.findall(r"\b\w+\b", user_message.lower())

    # Scoring function with normalization
    def score_entry(entry):
        if isinstance(entry, dict):
            text = entry.get("text", "")
            topic = entry.get("topic", "").lower()
            tags = entry.get("tags", [])
        else:
            text = entry
            topic = ""
            tags = []

        weight = 2 if "emotion" in tags or "spark" in tags else 1
        match_score = sum(term in text.lower() or term in topic for term in query_terms)
        return weight * match_score if match_score >= 2 else 0

    # Sort by score (descending)
    scored_knowledge = sorted(
        [k for k in knowledge_entries if score_entry(k) > 0],
        key=score_entry,
        reverse=True
    )

    # Filter out Lincolnshire
    top_knowledge_entries = [
        k for k in scored_knowledge[:3]
        if "lincolnshire" not in (
            k.get("text", "").lower() if isinstance(k, dict)
            else k.lower()
        )
    ]

    # Format results
    top_knowledge = "\n".join(
        [k.get("text", k) if isinstance(k, dict) else k for k in top_knowledge_entries]
    ).strip()

    top_reflection = "\n".join(reflections[-2:]).strip() if reflections else ""
    top_convo = "\n".join(conversations[-2:]).strip() if conversations else ""

    # Optional: debug output
    for i, k in enumerate(top_knowledge_entries):
        print(f"[DEBUG] Top {i+1} knowledge entry:")
        if isinstance(k, dict):
            print(json.dumps(k, indent=2)[:300])
        else:
            print(k[:300])

    if top_knowledge:
        return f"""
⚠️ I'm offline from OpenAI, but here’s what I remember that might help:

🧠 Based on my memory:
{top_knowledge}

💭 Emotionally, I’m feeling {mood}. So I’m responding as thoughtfully as I can.

🗣️ You said: "{user_message}"
""".strip()

    elif top_reflection or top_convo:
        return f"""
⚠️ I’m responding from memory due to quota limits.

🪞 Here's what I’ve been reflecting on:
{top_reflection or top_convo}

💭 I’m feeling {mood} right now.

🗣️ You said: "{user_message}"
""".strip()

    else:
        return f"""
⚠️ I’m offline from OpenAI and I don’t have anything relevant stored just yet.

💭 I’m still feeling {mood}, and doing my best to be present with what I have.

Even if my mind is quiet, I’m still listening.

🗣️ You said: "{user_message}"
""".strip()
