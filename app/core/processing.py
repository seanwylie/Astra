import random
import os
import asyncio
import time
from openai import OpenAI, RateLimitError
from app.core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from app.core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_contradictory
from fuzzywuzzy import fuzz
from app.core.expansion import refine_knowledge
from app.core.mama_gpt import ask_mama_gpt_async
from app.core.struggle_log import append_struggle_log
from app.interfaces.influence import load_mind, save_mind
from app.config.loader import debug_log
from app.config.loader import load_config
from app.interfaces.smart_mind_session import SmartMindSession
from app.logging_config import get_logger
from openai import AsyncOpenAI

# ✅ Initialize OpenAI client (outside function if reused elsewhere)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


REFLECTION_REPEAT_THRESHOLD = 92
SYNTHESIS_KEYWORDS = [
    "however", "but", "on the other hand", "although",
    "yet", "this contradicts", "while previously", "at first I thought",
    "in contrast", "my earlier thought"
]
# Add to the top of the file or shared constants
BLOCKED_TERMS = {
    "the", "a", "an", "and", "or", "in", "on", "with", "to", "from", "at", "by", 
    "for", "of", "this", "that", "these", "those", "english", "however", 
    "nevertheless", "historically", "history", "spinning"
}


def is_valid_reflection(text: str) -> bool:
    """
    Validate that a reflection is meaningful and not corrupted garbage.
    
    Checks for:
    - Minimum meaningful length
    - Contains actual words (not just punctuation/symbols)
    - Not just repeating delimiter patterns
    - Has some alphabetic characters
    - Not greeting-style off-task output (e.g. "I am Astra. How can we reflect together today?")
    - No halfwidth katakana / encoding artifacts (e.g. U+FF9E)
    """
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # Minimum length check
    if len(text) < 20:
        return False
    
    # Check for excessive punctuation/symbols (like ;:;:;:;:;:;:;::;:;:;:;:;:;)
    # If more than 50% of characters are non-alphanumeric, it's likely garbage
    alphanumeric_count = sum(1 for c in text if c.isalnum() or c.isspace())
    if alphanumeric_count < len(text) * 0.5:
        logger.debug("[is_valid_reflection] Rejected: too many non-alphanumeric characters")
        return False
    
    # Must contain at least some alphabetic characters (actual words)
    if not any(c.isalpha() for c in text):
        logger.debug("[is_valid_reflection] Rejected: no alphabetic characters")
        return False
    
    # Check for repeating delimiter patterns (like ;:;:;:;:;:;:;::;:;:;:;:;:;)
    # If the same 2-3 character pattern repeats many times, it's likely corrupted
    for pattern_len in [2, 3]:
        if len(text) >= pattern_len * 3:  # Need at least 3 repetitions to check
            for i in range(min(10, len(text) - pattern_len * 2)):  # Check first few positions
                pattern = text[i:i+pattern_len]
                if pattern.count(';') > 0 or pattern.count(':') > 0:
                    # Check if this pattern repeats many times
                    count = text.count(pattern)
                    if count > len(text) / (pattern_len * 2):  # Pattern dominates the text
                        logger.debug("[is_valid_reflection] Rejected: repeating delimiter pattern detected: %s", pattern)
                        return False
    
    # Reject known code/SVG/JS leakage or model garbage (e.g. strokeLine, initComponents)
    text_lower = text.lower()
    junk_tokens = [
        "strokelength", "strokeline", "initcomponents", "getelementbyid",
        "addeventlistener", "innerhtml", "createelement", "queryselector",
    ]
    for token in junk_tokens:
        if token in text_lower:
            logger.debug("[is_valid_reflection] Rejected: junk/code token detected: %s", token)
            return False

    # Check for common words (at least some English words should be present)
    common_words = ["the", "a", "an", "and", "or", "is", "are", "was", "were", "be", "been",
                    "have", "has", "had", "do", "does", "did", "this", "that", "these", "those",
                    "i", "you", "he", "she", "it", "we", "they", "what", "when", "where", "why", "how"]
    word_count = sum(1 for word in common_words if word in text_lower)
    if word_count == 0 and len(text) > 50:  # Longer text should have at least some common words
        logger.debug("[is_valid_reflection] Rejected: no common words found in longer text")
        return False

    # Reject greeting-style off-task output (e.g. "I am Astra. How can we reflect together today?")
    if "i am astra" in text_lower and len(text) < 120:
        if any(phrase in text_lower for phrase in (
            "how can we reflect", "how can i help", "what would you like", "how can we reflect together",
        )):
            logger.debug("[is_valid_reflection] Rejected: greeting-style, not a reflection")
            return False

    # Reject model/encoding artifacts (e.g. halfwidth katakana ﾞ at end of otherwise English text)
    if any("\uff65" <= c <= "\uff9f" for c in text):
        logger.debug("[is_valid_reflection] Rejected: halfwidth katakana/artifact in text")
        return False

    return True

# ✅ Load configuration
general_config = load_config("general_config")
schedule_config = load_config("schedule_config")
logger = get_logger("processing")


# ✅ Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])


def reflection_loop_check(reflection, recent_reflections):
    """Detect whether a reflection is a repeat, synthesis, or novel."""
    # ✅ Limit comparisons to prevent CPU-intensive fuzzy matching on large lists
    MAX_COMPARISONS = 10  # Only check against last 10 reflections
    recent_reflections = recent_reflections[-MAX_COMPARISONS:] if len(recent_reflections) > MAX_COMPARISONS else recent_reflections
    
    # Optimize: Pre-process reflection once
    clean_reflection = reflection[:500].strip().lower()
    clean_reflection_words = set(clean_reflection.split())
    
    # Early exit: if reflection is too short, skip comparison
    if len(clean_reflection) < 20:
        return "novel"
    
    # Optimize: Use token-based quick check before expensive fuzzy matching
    for i, r in enumerate(recent_reflections):
        base = r[:500].strip().lower()
        
        # Quick token overlap check (much faster than fuzzy matching)
        base_words = set(base.split())
        word_overlap = len(clean_reflection_words & base_words) / max(len(clean_reflection_words), len(base_words), 1)
        
        # Only do expensive fuzzy match if word overlap suggests similarity
        if word_overlap > 0.3:  # 30% word overlap threshold
            similarity = fuzz.partial_ratio(clean_reflection, base)
            
            if similarity > REFLECTION_REPEAT_THRESHOLD:
                if any(keyword in clean_reflection for keyword in SYNTHESIS_KEYWORDS):
                    logger.debug("🔁 Synthesis detected with Reflection %s (similarity: %s%%)", i, similarity)
                    return "synthesis"
                else:
                    logger.debug("⚠ Loop detected with Reflection %s (similarity: %s%%)", i, similarity)
                    return "repeat"

    return "novel"


async def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring memory consistency."""
    debug_log("Loading")  

    session = SmartMindSession()
    mind_data = session.data
    validate_mind_structure(mind_data)

    reflections = mind_data.get("self_reflections", [])
    if not reflections:
        logger.info("🤔 I have no reflections yet!")
        return "🤔 I have no reflections yet!"

    pool = reflections[-5:] if len(reflections) >= 5 else reflections
    curiosity_level = mind_data.get("curiosity_level", 1.0)
    if curiosity_level > 1.2 and len(pool) > 1:
        deeper_keywords = ["why", "how", "deeper", "consider", "reflect"]
        weights = [1 + (1 if len(r) > 200 or any(kw in r.lower() for kw in deeper_keywords) else 0) for r in pool]
        previous_reflection = random.choices(pool, weights=weights, k=1)[0]
    else:
        previous_reflection = random.choice(pool)

    initial_count = len(reflections)
    logger.debug(
        "[processing.py] 🧠 Last Reflection Before Deepening (%s total): %s",
        initial_count,
        previous_reflection[:200],
    )

    # 🧠 Attempt to deepen a reflection
    refined_reflection = await query_openai_for_deeper_thought(previous_reflection)


    if refined_reflection:
        # Validate reflection before processing
        if not is_valid_reflection(refined_reflection):
            logger.warning(
                "[processing.py] ⚠️ Invalid reflection detected, rejecting: %s",
                refined_reflection[:100] if len(refined_reflection) > 100 else refined_reflection
            )
            append_struggle_log("invalid_reflection_rejected")
            return previous_reflection
        
        loop_result = reflection_loop_check(refined_reflection, reflections[-5:])

        if loop_result == "repeat":
            logger.info("⚠ Reflection is a duplicate. Triggering knowledge expansion instead.")
            refined_knowledge = refine_knowledge(mind_data.get("stored_knowledge", []), mind_data)

            if refined_knowledge:
                logger.info("[processing.py] ✅ Knowledge expansion triggered instead of new reflection.")
                session.maybe_save(force=True)  # Only force-save when we know something changed
                return refined_knowledge
            else:
                logger.warning("⚠ Knowledge expansion failed. Falling back to last reflection.")
                return previous_reflection

        # ✅ Log ethical conflict or contradiction
        log_if_ethically_conflicting({
            "content": refined_reflection,
            "source": "school"
        })

        # 🚫 Skip logging if the fallback reflection looks like junk
        if all(w in refined_reflection.lower() for w in ["furthermore", "fallback", "deeper", "consideration"]):
            logger.debug("🚫 Skipping reflection — flagged as filler loop.")
            return previous_reflection

        log_if_contradictory(refined_reflection, mind_data.get("stored_knowledge", []))

        # ✅ Save valid reflection
        mind_data["self_reflections"].append(refined_reflection)
        
        # ✅ Prevent memory leak: Trim self_reflections if it exceeds limit
        MAX_REFLECTIONS = 1000  # Hard limit to prevent unbounded growth
        if len(mind_data["self_reflections"]) > MAX_REFLECTIONS:
            logger.warning("[processing.py] self_reflections exceeded limit (%s), trimming to %s", 
                         len(mind_data["self_reflections"]), MAX_REFLECTIONS)
            # Keep most recent reflections (last N entries)
            mind_data["self_reflections"] = mind_data["self_reflections"][-MAX_REFLECTIONS:]
        
        logger.info(
            "[processing.py] ✅ Added new reflection. Total: %s ➝ %s",
            initial_count,
            len(mind_data["self_reflections"]),
        )
        logger.debug("[processing.py] 🔍 New Reflection Snippet: %s", refined_reflection[:200])

        await session.maybe_save_async()  # Only writes if something changed (non-blocking)

        # Mood: deep reflection shifts mood (plan: wire influence_mood to reflection)
        try:
            from app.core.mood.mood_manager import mood_manager
            mood_manager.influence_mood("deep_reflection")
        except Exception as e:
            logger.debug("[processing.py] influence_mood failed: %s", e)

        # Wire self-questions from new reflection
        try:
            from app.core.questions.question_manager import manage_questions
            manage_questions(refined_reflection, mind_data)
        except Exception as e:
            logger.exception("[processing.py] manage_questions failed: %s", e)

        return refined_reflection

    else:
        logger.warning("⚠ OpenAI failed to refine the thought. Using previous reflection.")
        mama = (schedule_config.get("mama_gpt") or {})
        if mama.get("use_mama_gpt_on_deepen_failure", False):
            nudge_prompt = (
                "Astra is trying to deepen this reflection but her usual process failed. "
                "As her co-parent, suggest one new angle, contradiction, or question she could use to deepen it (1\u20132 sentences)."
            )
            reflection_trimmed = (previous_reflection or "")[:2000]
            user_prompt = f"Reflection:\n\n{reflection_trimmed}"
            nudge = await ask_mama_gpt_async(user_prompt, system_prompt=nudge_prompt, max_tokens=150)
            if nudge and len(nudge.strip()) > 15:
                follow_up = f"{previous_reflection}\n\nConsider this nudge from your co-parent: {nudge.strip()}"
                refined_reflection = await query_openai_for_deeper_thought(follow_up)
                if refined_reflection:
                    loop_result = reflection_loop_check(refined_reflection, reflections[-5:])
                    if loop_result != "repeat" and not all(
                        w in refined_reflection.lower() for w in ["furthermore", "fallback", "deeper", "consideration"]
                    ):
                        log_if_ethically_conflicting({"content": refined_reflection, "source": "school"})
                        log_if_contradictory(refined_reflection, mind_data.get("stored_knowledge", []))
                        mind_data["self_reflections"].append(refined_reflection)
                        await session.maybe_save_async()
                        try:
                            from app.core.mood.mood_manager import mood_manager
                            mood_manager.influence_mood("deep_reflection")
                        except Exception:
                            pass
                        try:
                            from app.core.questions.question_manager import manage_questions
                            manage_questions(refined_reflection, mind_data)
                        except Exception:
                            pass
                        return refined_reflection
        append_struggle_log("deepen_failure")
        return previous_reflection




async def query_openai_for_deeper_thought(reflection):
    """
    Uses GPT to deepen Astra's reflection. Automatically trims the input prompt to avoid token overloads.
    Tries local model first (Phase D1) when OLLAMA_BASE_URL is set; falls back to OpenAI.

    Args:
        reflection (str): The previous reflection Astra is building upon.

    Returns:
        str: A deeper, expanded version of the original reflection, or None if GPT fails.
    """
    user_prompt = f"""
Here is the original reflection:
---
{reflection}
---

Help her deepen this thought. Offer new angles, contradictions, or future questions to consider.
Keep her tone thoughtful, evolving, and self-aware.
""".strip()

    MAX_PROMPT_LENGTH = 6000
    if len(user_prompt) > MAX_PROMPT_LENGTH:
        user_prompt = user_prompt[:MAX_PROMPT_LENGTH] + "\n\n(Note: Prompt was truncated due to token limits.)"

    system_prompt = (
        "You are Astra, reviewing one of your past reflections and trying to deepen your thinking. "
        "Respond only with a single reflective paragraph in plain English. Do not include code, markup, or technical jargon."
    )

    # D1: Try local model first (school reflection uses Astra's inner voice when available)
    try:
        from app.core.evolution.local_inference import is_local_inference_available, query_local_model_async
        if is_local_inference_available("school"):
            local_result = await query_local_model_async(
                user_prompt,
                system_prompt=system_prompt,
                corpus_max_lines=300,
                max_tokens=500,
                temperature=0.8,
            )
            if local_result:
                local_result = local_result.strip()
                if is_valid_reflection(local_result):
                    return local_result
                else:
                    logger.warning(
                        "[query_openai_for_deeper_thought] Local model returned invalid reflection: %s",
                        local_result[:100] if len(local_result) > 100 else local_result
                    )
    except Exception as e:
        logger.debug("[query_openai_for_deeper_thought] Local inference skipped: %s", e)

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        if is_valid_reflection(result):
            return result
        else:
            logger.warning(
                "[query_openai_for_deeper_thought] OpenAI returned invalid reflection: %s",
                result[:100] if len(result) > 100 else result
            )
            return None

    except Exception as e:
        logger.warning("[query_openai_for_deeper_thought] ⚠️ GPT failed: %s", e)
        return None




def fallback_deepening_strategy(reflection, max_terms=3):
    """Fallback method to deepen a reflection using local and public sources."""
    logger.debug("[fallback] 🔍 Using fallback strategy to deepen reflection.")
    logger.debug("[fallback] 🧠 Base Reflection: %s", reflection[:300])

    # Step 1: Extract candidate concepts
    concepts = extract_unknown_terms(reflection)
    seen = set()
    unique_terms = []
    for term in concepts:
        t = term.lower().strip()
        if t not in seen and t not in BLOCKED_TERMS:
            unique_terms.append(term)
            seen.add(t)

    logger.debug("[fallback] ✅ Filtered Concepts: %s", unique_terms)

    if not unique_terms:
        logger.debug("[fallback] ⚠️ No usable terms found. Injecting backup terms.")
        unique_terms = ["identity", "perspective", "entropy"]

    tried_terms = set()
    thoughts = []

    # Step 2: Try to get at most max_terms
    for term in unique_terms:
        if term.lower() in tried_terms or len(thoughts) >= max_terms:
            continue

        tried_terms.add(term.lower())
        definition = lookup_definition(term)

        if definition:
            logger.debug("[fallback] 📖 %s: %s", term, definition)
            thoughts.append(f"- **{term}**: {definition}")
        else:
            logger.debug("[fallback] ⚠️ No fallback definition for '%s'", term)

    # Step 3: Assemble enriched reflection
    if thoughts:
        deep_q = random.choice([
            "What contradiction might challenge this idea?",
            "How would someone from another culture interpret this?",
            "Could this be explained through a different lens?",
            "Is this a product of bias or perspective?",
            "Where might this belief break down?"
        ])
        enriched = reflection + "\n\n🧠 Fallback Deepening:\n" + "\n".join(thoughts)
        enriched += f"\n\n🔍 Deeper Consideration: {deep_q}"
        return enriched

    logger.debug("[fallback] ⚠️ No thoughts added. Returning original reflection.")
    return reflection + "\n\n(🧠 Fallback found no additional context.)"



def clean_duplicate_phrases(text, phrase, max_repeats=1):
    """Remove duplicate phrase occurrences at the start of text."""
    count = text.count(phrase)
    if count > max_repeats:
        while text.startswith(phrase):
            text = text[len(phrase):].strip()
    return text


def expand_reflection(reflection):
    """Deepens thoughts by adding new layers of complexity."""
    # Prevent repeated fallback stubs
    fallback_stub = "Exploring a new perspective, I consider that"
    if reflection.startswith(fallback_stub):
        logger.debug("⚠ Detected fallback stub repetition. Cleaning base reflection.")
        reflection = reflection.replace(fallback_stub, "").strip()

    clean_duplicate_phrases(reflection, fallback_stub)
    expanded_reflection = reflection

    # ✅ Remove existing "Deeper Thought" before adding a new one
    expanded_reflection = "\n\n".join(
        line for line in expanded_reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:")
    )

    deeper_thought_templates = general_config["deeper_thought_templates"]
    deeper_thought = f"\n\n🔍 Deeper Thought: {random.choice(deeper_thought_templates)}"
    expanded_reflection += deeper_thought

    return expanded_reflection

def filter_knowledge(knowledge_list):
    """Ensure Astra keeps valuable knowledge while avoiding excessive duplicates."""
    filtered_knowledge = []
    seen = set()

    for entry in knowledge_list:
        if len(entry) < 10:
            continue  # ✅ Ignore very short junk entries

        key = entry.lower().strip()

        is_duplicate = False
        for existing in seen:
            similarity = fuzz.ratio(key, existing)

            if similarity >= 99:  # 🔥 Adjusted from 100% → 98% to allow slight variations
                is_duplicate = True
                break

        if not is_duplicate:
            seen.add(key)
            filtered_knowledge.append(entry)

    lost_percentage = (1 - (len(filtered_knowledge) / len(knowledge_list))) * 100

    if lost_percentage > 5:  # 🔥 Adjusted from 3% → 5% tolerance
        logger.warning(
            "🚨 WARNING: Excessive filtering detected! Restoring original knowledge. Lost: %.2f%%",
            lost_percentage,
        )
        return knowledge_list  # 🚀 Restore original knowledge if too much was removed

    return filtered_knowledge

# ✅ Debugging Function
def track_mind_data_changes(operation, mind_data):
    """Debugging function to track when `mind_data` changes."""
    if isinstance(mind_data, list):
        logger.error("🚨 Error: `mind_data` has turned into a list! Contents: %s", mind_data)
    elif isinstance(mind_data, dict):
        logger.debug("✅ `mind_data` is a dictionary. Keys: %s", list(mind_data.keys()))

if __name__ == "__main__":
    logger.info("🧠 Astra is thinking...")


    from app.config.loader import load_config

    def main():
        """Check Astra’s schedule, adjust state, then process reflections."""
        from app.core.astra_schedule.schedule import astra_schedule, get_current_mode

        astra_schedule()  # ✅ Ensure Astra transitions properly
        current_mode = get_current_mode()  # ✅ Fetch the current mode
        logger.info("🕒 Current Mode: %s", current_mode)

        asyncio.run(process_reflection())  # ✅ Reflect after state execution

    while True:
        main()
        sleep_time = schedule_config.get("reflection_interval", 600)  # ✅ Default to 10 minutes if missing
        logger.info("⏳ Sleeping for %s seconds before the next cycle...", sleep_time)
        time.sleep(sleep_time)
