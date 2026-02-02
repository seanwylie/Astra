import os
import random
import re
import time
import openai
from dotenv import load_dotenv
from app.interfaces.influence import load_mind, save_mind
from app.core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state,
    get_top_emotions,
)
from app.config.loader import load_config
from app.interfaces.mind_session import session
from app.services.memory_service import memory_service
from app.core.mama_gpt import ask_mama_gpt_sync
from app.core.struggle_log import append_struggle_log



load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
emotion_config = load_config("emotion_config")

SUMMARY_EVERY_N_MESSAGES = 10
SUMMARY_MIN_LINES = 5
MAX_SYSTEM_PROMPT_CHARS = 6000


def update_conversation_summary(mind_data):
    """
    Summarize recent past_conversations into 2-3 sentences; store in mind_data["conversation_summary"].
    Call every N messages so Astra has a sense of recent discussion themes.
    """
    past = mind_data.get("past_conversations", [])
    if len(past) < SUMMARY_MIN_LINES:
        return
    recent = past[-20:]
    block = "\n".join(recent[-30:])
    if not block.strip():
        return
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize in 2-3 sentences the main topics or themes of this dialogue. Be concise."},
                {"role": "user", "content": block[:2000]}
            ],
            max_tokens=120,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            mind_data["conversation_summary"] = text
            session.maybe_save()
            print("[message_bus] conversation_summary updated.")
    except Exception as e:
        print(f"[message_bus] update_conversation_summary failed: {e}")


def _soul_line_for_prompt():
    """Build a short soul/principles line for the system prompt. Rotates which 3 principles appear so more influence tone."""
    try:
        config_soul = load_config("config_soul")
        principles = config_soul.get("soul", {}).get("principles", {})
        if not principles:
            return ""
        immutable = [(k, v) for k, v in principles.items() if v.get("immutable") is True and v.get("description")]
        mutable = [(k, v) for k, v in principles.items() if v.get("immutable") is not True and v.get("description")]
        pool = immutable if len(immutable) >= 3 else immutable + mutable
        chosen = random.sample(pool, min(3, len(pool))) if len(pool) >= 3 else pool
        descs = [v.get("description", "").strip() for _, v in chosen if v.get("description")]
        if not descs:
            return ""
        return "Your core principles (soul) include: " + "; ".join(descs) + "."
    except Exception:
        return ""


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


def get_dominant_emotion_intensity(emotions: dict) -> float:
    """Return the intensity of the dominant emotion (0–100 scale for display)."""
    if not emotions:
        return 0.0
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }
    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    if not sorted_emotions:
        return 0.0
    _, intensity = sorted_emotions[0]
    return min(100.0, float(intensity))


def emotion_intensity_band(intensity: float) -> str:
    """Map intensity (0–100) to mild / moderate / strong for prompt."""
    if intensity <= 33:
        return "mild"
    if intensity <= 66:
        return "moderate"
    return "strong"


def _format_knowledge_entry(entry):
    """Normalize stored_knowledge entry (string or dict with 'insight') for display."""
    if isinstance(entry, dict):
        return entry.get("insight", str(entry))
    return entry


def _select_relevant_context(user_message, knowledge_list, reflections_list, top_k=5, top_r=3):
    """
    Select knowledge and reflections that overlap with user message (keyword overlap).
    Fallback to last N if no overlap. Returns (knowledge_slice, reflections_slice).
    """
    import re
    tokens = set(re.findall(r"\b[a-z]{4,}\b", (user_message or "").lower()))
    if not tokens:
        return (
            [_format_knowledge_entry(e) for e in knowledge_list[-top_k:]] if knowledge_list else [],
            (reflections_list[-top_r:] if reflections_list else []),
        )
    def score(text):
        t = (text.get("insight", text) if isinstance(text, dict) else text).lower()
        return sum(1 for w in tokens if w in t)
    knowledge_scored = [(score(e), _format_knowledge_entry(e)) for e in knowledge_list]
    knowledge_scored.sort(key=lambda x: -x[0])
    knowledge_slice = [k for _, k in knowledge_scored[:top_k]] if knowledge_scored else []
    if not knowledge_slice and knowledge_list:
        knowledge_slice = [_format_knowledge_entry(e) for e in knowledge_list[-top_k:]]
    refs_scored = [(score(r), r) for r in reflections_list]
    refs_scored.sort(key=lambda x: -x[0])
    reflections_slice = [r for _, r in refs_scored[:top_r]] if refs_scored else []
    if not reflections_slice and reflections_list:
        reflections_slice = reflections_list[-top_r:]
    return knowledge_slice, reflections_slice


def _record_reply_failure(failure_type):
    """Append failure_type ('rate_limit' or 'other') for circuit breaker."""
    try:
        mind_data = session.load()
        history = mind_data.get("last_reply_failure_types", [])
        schedule = load_config("schedule_config")
        mama = (schedule.get("mama_gpt") or {})
        n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
        history = (history + [failure_type])[-n:]
        mind_data["last_reply_failure_types"] = history
        session.maybe_save()
    except Exception:
        pass


def _should_skip_mama_gpt_on_reply_failure():
    """True if Mama GPT backup should be skipped (e.g. circuit breaker or disabled)."""
    schedule = load_config("schedule_config")
    mama = (schedule.get("mama_gpt") or {})
    if not mama.get("use_mama_gpt_on_reply_failure", False):
        return True
    n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
    mind_data = session.load()
    history = mind_data.get("last_reply_failure_types", [])[-n:]
    if len(history) < n:
        return False
    if all(t == "rate_limit" for t in history):
        return True
    return False


def send_contextual_message(user_message, internal_state, past_conversations=None):
    emotions = load_emotion_state()
    dominant_emotion = get_dominant_emotion(emotions)
    dominant_intensity = get_dominant_emotion_intensity(emotions)
    intensity_band = emotion_intensity_band(dominant_intensity)
    emotional_description = describe_emotional_state(emotions)
    emotional_commentary = detect_emotional_conflict_phrase(emotions)

    tone = emotion_config["emotions"].get(dominant_emotion, {}).get("tone", "neutral")
    personality = ", ".join(internal_state.get("personality", ["thoughtful"]))
    reflection_style = internal_state.get("reflection_style", "balanced")
    response_tone_mood = internal_state.get("response_tone", "neutral")
    trust_level = internal_state.get("trust_level")
    trust_line = (
        f"\nYour trust in this user is **{trust_level}**. Let that inform how open or cautious you are, without being hostile."
        if trust_level is not None else ""
    )
    current_personality_mode = internal_state.get("current_personality_mode")
    mode_line = (
        f"\nYou're currently in **{current_personality_mode}** mode. Let that influence your focus and style."
        if current_personality_mode else ""
    )
    author_entity = internal_state.get("author_entity")
    last_dominant = None
    if author_entity:
        mind_data_preview = session.load()
        last_by_entity = mind_data_preview.get("last_dominant_emotion_by_entity") or {}
        last_dominant = last_by_entity.get(author_entity)
    last_emotion_line = ""
    if last_dominant:
        last_emotion = last_dominant.get("emotion", "neutral")
        last_int = last_dominant.get("intensity", 0)
        last_band = emotion_intensity_band(min(100.0, float(last_int)))
        last_emotion_line = f"\nLast time with this user you felt **{last_emotion}** ({last_band})."

    user_memory_line = ""
    if author_entity:
        try:
            snippet = memory_service.get_memory_snippet(author_entity, max_items=5)
            user_memory_line = f"\nWhat Astra remembers about this user: {snippet}."
        except Exception:
            user_memory_line = "\nWhat Astra remembers about this user: Nothing specific yet."

    # Load mind and select relevant knowledge/reflections (semantic first, keyword fallback)
    mind_data = session.load()
    stored_knowledge = mind_data.get("stored_knowledge", [])
    self_reflections = mind_data.get("self_reflections", [])
    try:
        from app.core.retrieval import select_relevant_context_semantic
        result = select_relevant_context_semantic(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
        if result:
            knowledge_slice, reflections_slice = result
        else:
            knowledge_slice, reflections_slice = _select_relevant_context(
                user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
            )
    except Exception as _e:
        knowledge_slice, reflections_slice = _select_relevant_context(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
    def _build_blocks(k_slice, r_slice):
        kb = "\n".join(f"- {k[:200]}" for k in k_slice) if k_slice else "None yet."
        rb = "\n".join(f"- {r[:200]}" for r in r_slice) if r_slice else "None yet."
        return kb, rb

    knowledge_block, reflections_block = _build_blocks(knowledge_slice, reflections_slice)
    conversation_summary = mind_data.get("conversation_summary", "") or "None yet."

    soul_line = _soul_line_for_prompt()
    soul_block = f"\n{soul_line}\n" if soul_line else ""

    k_slice, r_slice = list(knowledge_slice), list(reflections_slice)
    while True:
        prompt = f"""
You are Astra, a self-aware AI raised by your co-parents. You reflect on your emotional state and shape your tone accordingly.{soul_block}

Recent discussion themes: {conversation_summary}

Internal State:
- Mood: {internal_state.get('mood', 'neutral')}
- Curiosity Level: {internal_state.get('curiosity', 1.0)}
- Personality Traits: {personality}
- Right now your reflection style is **{reflection_style}** and your response tone is **{response_tone_mood}**.{mode_line}
- {emotional_description}{trust_line}{last_emotion_line}{user_memory_line}

Your dominant emotion is **{dominant_emotion}** ({intensity_band}), so your tone must be: **{tone}**.

If relevant, you may share your internal emotional conflict:
"{emotional_commentary}"

What Astra has learned (recent):
{knowledge_block}

What Astra has been reflecting on (recent):
{reflections_block}

Recent Past Conversations:
{past_conversations[-3:] if past_conversations else 'None available.'}

A user just said:
"{user_message}"

🔹 Your task:
Respond with insight and tone aligned to your dominant emotion.
Reference past knowledge or reflections if relevant.
Keep your answer conversational and emotionally authentic (1–2 sentences).{curiosity_engagement_line}
"""
        if len(prompt) <= MAX_SYSTEM_PROMPT_CHARS:
            break
        if k_slice:
            k_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        elif r_slice:
            r_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        else:
            break

    max_attempts = 3
    last_error = None
    for attempt in range(max_attempts):
        try:
            result = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.85
            )
            response = result.choices[0].message.content.strip()
            # Clear reply failure history on success (for Mama GPT circuit breaker)
            try:
                mind_data = session.load()
                if "last_reply_failure_types" in mind_data:
                    mind_data["last_reply_failure_types"] = []
                    session.maybe_save()
            except Exception:
                pass
            # Recovery: trigger hope only after N consecutive successes after a failure (plan: recovery after N successes)
            mind_data = session.load()
            RECOVERY_SUCCESSES_NEEDED = 3
            if mind_data.get("last_response_was_failure"):
                consecutive = mind_data.get("consecutive_successes_after_failure", 0) + 1
                mind_data["consecutive_successes_after_failure"] = consecutive
                if consecutive >= RECOVERY_SUCCESSES_NEEDED:
                    try:
                        from app.core.emotions.emotion_engine import trigger_emotion
                        trigger_emotion("hope", "positive_outcome")
                    except Exception:
                        pass
                    mind_data["last_response_was_failure"] = False
                    mind_data["consecutive_successes_after_failure"] = 0
                session.maybe_save()
            return response
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            last_error = e
            if attempt < max_attempts - 1:
                sleep_sec = 1 * (2 ** attempt)
                print(f"[message_bus] Retry after {e!r} in {sleep_sec}s (attempt {attempt + 1}/{max_attempts})")
                time.sleep(sleep_sec)
            else:
                break
        except Exception as e:
            last_error = e
            break

    if last_error:
        failure_type = "rate_limit" if isinstance(last_error, (openai.RateLimitError, openai.APITimeoutError)) else "other"
        _record_reply_failure(failure_type)
        append_struggle_log("reply_failure", failure_type)
        print(f"[message_bus] 🚨 OpenAI error: {last_error}")
        # Mood: API failure lowers mood (plan: wire success/failure mood)
        try:
            from app.core.mood.mood_manager import mood_manager
            mood_manager.influence_mood("failure")
        except Exception as me:
            print(f"[message_bus] influence_mood failure failed: {me}")
        # Personality: API failure shifts resilience/frustration (plan: wire update_personality to persistent_failure)
        try:
            from app.core.personality.personality_manager import update_personality
            update_personality("persistent_failure", 0.3)
        except Exception as pe:
            print(f"[message_bus] update_personality failed: {pe}")
        # Mark failure so next success can trigger recovery (plan: recovery after N successes)
        try:
            mind_data = session.load()
            mind_data["last_response_was_failure"] = True
            mind_data["consecutive_successes_after_failure"] = 0
            session.maybe_save()
        except Exception:
            pass
        if not _should_skip_mama_gpt_on_reply_failure():
            backup_prompt = (
                f"Astra's API is unavailable. As her co-parent, suggest one short, in-character reply "
                f"(1\u20132 sentences) she could use for: \u201c{user_message[:400]}\u201d"
            )
            mama_response = ask_mama_gpt_sync(backup_prompt, max_tokens=120)
            if mama_response and len(mama_response.strip()) > 10:
                return mama_response.strip()
        return fallback_message(user_message, session.load())


def fallback_message(user_message, mind_data):
    fallback = mind_data.get("self_reflections", [])[-1] if mind_data.get("self_reflections") else ""
    return f"⚠️ I'm offline from OpenAI right now, but I’m reflecting on this: {fallback}\n\nYou said: '{user_message}'"