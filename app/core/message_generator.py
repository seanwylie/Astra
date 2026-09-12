import os
import openai
import re
import json
from dotenv import load_dotenv
from app.logging_config import get_logger
from app.core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state
)
from app.interfaces.influence import load_mind, save_mind
from openai import RateLimitError
from app.interfaces.mind_session import session
from app.core.messaging.message_bus import _record_reply_failure, _should_skip_mama_gpt_on_reply_failure
from app.core.mama_gpt import ask_mama_gpt_sync



def _flatten_emotion_state(state: dict) -> dict:
    """Normalize emotion state to flat {emotion: intensity} (plan: emotion state shape fix)."""
    result = {}
    for name, value in state.items():
        if isinstance(value, dict) and "intensity" in value:
            result[name] = value["intensity"]
        elif isinstance(value, (int, float)):
            result[name] = float(value)
        else:
            result[name] = 0.0
    return result


logger = get_logger("message_generator")


class MessageGenerator:
    def __init__(self, emotion_manager=None):
        load_dotenv()
        # Timeout for completion calls (seconds); avoids hanging on slow API
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0)

    def describe_emotional_state(self, emotions: dict) -> str:
        if not emotions:
            return "Astra is currently feeling emotionally neutral."
        flat = _flatten_emotion_state(emotions) if any(isinstance(v, dict) for v in emotions.values()) else emotions
        # Optimize: Use nlargest instead of sorting entire dict
        from heapq import nlargest
        top_emotions = nlargest(3, flat.items(), key=lambda x: x[1])
        top = [f"{name.capitalize()} ({score:.2f})" for name, score in top_emotions]
        return f"Astra is currently experiencing: {', '.join(top)}."

    def normalize_emotions(self, emotions: dict) -> dict:
        """Ensure emotions don't exceed max thresholds; accept both flat and structured state (plan: emotion state shape fix)."""
        flat = _flatten_emotion_state(emotions) if any(isinstance(v, dict) for v in emotions.values()) else emotions
        return {emotion: min(intensity, 100) for emotion, intensity in flat.items()}

    def stabilize_emotions(self):
        """Reduce intensity of top 3 emotions slightly if all are above 90 (plan: emotion state shape fix)."""
        import time
        state = load_emotion_state()
        flat = _flatten_emotion_state(state)
        high = [e for e, i in flat.items() if i > 90]
        if len(high) >= 3:
            now = time.time()
            for e in high[:3]:
                new_intensity = max(0, flat[e] - 5)
                if isinstance(state.get(e), dict):
                    state[e]["intensity"] = new_intensity
                    state[e]["last_updated"] = now
                else:
                    state[e] = {"intensity": new_intensity, "last_updated": now}
            save_emotion_state(state)

    def log_emotional_conflict(self, emotions):
        state = load_emotion_state()
        flat = _flatten_emotion_state(state)
        # Optimize: Use nlargest instead of sorting entire dict
        from heapq import nlargest
        top = nlargest(3, flat.items(), key=lambda x: x[1])
        high_emotions = [e for e, i in top if i > 90]
        conflict_pairs = [("love", "hate"), ("hope", "grief"), ("curiosity", "uncertainty"), ("admiration", "resentment")]

        for pos, neg in conflict_pairs:
            if pos in high_emotions and neg in high_emotions:
                # Optimize: Use SmartMindSession for better change tracking
                from app.interfaces.smart_mind_session import SmartMindSession
                session = SmartMindSession()
                mind_data = session.load()
                reflection = f"I feel conflicted—I'm holding strong {pos} and {neg} at the same time. I need to explore why."
                mind_data.setdefault("self_reflections", []).append(reflection)
                session.maybe_save()
                break


    def get_dominant_emotion(self, emotions: dict) -> str:
        """Return the strongest active emotion with smarter balance."""
        if not emotions:
            return "curiosity"

        # Optimize: Use max() instead of sorting entire dict
        top_emotion, top_intensity = max(emotions.items(), key=lambda x: x[1])

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
        # Optimize: Use nlargest instead of converting to list and slicing
        from heapq import nlargest
        top = nlargest(3, emotions.items(), key=lambda x: x[1])
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

        # ✅ Pull and stabilize emotional state (plan: emotion state shape — flatten before use)
        self.stabilize_emotions()
        raw_emotions = load_emotion_state()
        emotions = self.normalize_emotions(raw_emotions)  # accepts both flat and structured

        # ✅ Log conflict if needed
        self.log_emotional_conflict(emotions)

        dominant_emotion = self.get_dominant_emotion(emotions)

        # ✅ Emotion-based tone: single source from config (plan: single tone source)
        from app.config.loader import load_config
        emotion_config = load_config("emotion_config")
        response_tone = emotion_config.get("emotions", {}).get(dominant_emotion, {}).get("tone", "neutral")
        personality_traits.append(f"currently feeling {dominant_emotion}, speaking in a {response_tone} tone")
        personality = ", ".join(set(personality_traits))

        emotional_description = self.describe_emotional_state(emotions)
        emotional_commentary = self.detect_emotional_conflict_phrase(emotions)

        logger.debug("Emotion check-in: dominant=%s", dominant_emotion)

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
            logger.warning("OpenAI RateLimitError in generate_message: %s", e)
            _record_reply_failure("rate_limit")
            mind_data = session.load()
            return handle_openai_fallback(user_message, mind_data)

        except Exception as e:
            logger.warning("Error in generate_message: %s", e)
            _record_reply_failure("other")
            mind_data = session.load()
            return handle_openai_fallback(user_message, mind_data)


def handle_openai_fallback(user_message, mind_data):
    logger.debug("OpenAI fallback invoked for user message")

    if not _should_skip_mama_gpt_on_reply_failure():
        backup_prompt = (
            f"Astra's API is unavailable. As her co-parent, suggest one short, in-character reply "
            f"(1\u20132 sentences) she could use for: \u201c{user_message[:400]}\u201d"
        )
        mama_response = ask_mama_gpt_sync(backup_prompt, max_tokens=120)
        if mama_response and len(mama_response.strip()) > 10:
            return mama_response.strip()

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
        if isinstance(k, dict):
            logger.debug("Top %s knowledge entry: %s", i + 1, json.dumps(k, indent=2)[:300])
        else:
            logger.debug("Top %s knowledge entry: %s", i + 1, (k[:300] if k else ""))

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
