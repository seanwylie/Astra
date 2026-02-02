import random
import os
import sys
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
from openai import AsyncOpenAI

# ✅ Ensure Python knows where to find Astra’s core modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


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

# ✅ Load configuration
general_config = load_config("general_config")
schedule_config = load_config("schedule_config")


# ✅ Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])


REFLECTION_REPEAT_THRESHOLD = 92
SYNTHESIS_KEYWORDS = [
    "however", "but", "on the other hand", "although",
    "yet", "this contradicts", "while previously", "at first I thought",
    "in contrast", "my earlier thought"
]


def reflection_loop_check(reflection, recent_reflections):
    """Detect whether a reflection is a repeat, synthesis, or novel."""
    clean_reflection = reflection[:500].strip().lower()

    for i, r in enumerate(recent_reflections):
        base = r[:500].strip().lower()
        similarity = fuzz.partial_ratio(clean_reflection, base)

        if similarity > REFLECTION_REPEAT_THRESHOLD:
            if any(keyword in clean_reflection for keyword in SYNTHESIS_KEYWORDS):
                print(f"🔁 Synthesis detected with Reflection {i} (similarity: {similarity}%)")
                return "synthesis"
            else:
                print(f"⚠ Loop detected with Reflection {i} (similarity: {similarity}%)")
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
        print("🤔 I have no reflections yet!")
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
    print(f"[processing.py] 🧠 Last Reflection Before Deepening ({initial_count} total):\n{previous_reflection[:200]}...")

    # 🧠 Attempt to deepen a reflection
    refined_reflection = await query_openai_for_deeper_thought(previous_reflection)


    if refined_reflection:
        loop_result = reflection_loop_check(refined_reflection, reflections[-5:])

        if loop_result == "repeat":
            print("⚠ Reflection is a duplicate. Triggering knowledge expansion instead.")
            refined_knowledge = refine_knowledge(mind_data.get("stored_knowledge", []), mind_data)

            if refined_knowledge:
                print("[processing.py] ✅ Knowledge expansion triggered instead of new reflection.")
                session.maybe_save(force=True)  # Only force-save when we know something changed
                return refined_knowledge
            else:
                print("⚠ Knowledge expansion failed. Falling back to last reflection.")
                return previous_reflection

        # ✅ Log ethical conflict or contradiction
        log_if_ethically_conflicting({
            "content": refined_reflection,
            "source": "school"
        })

        # 🚫 Skip logging if the fallback reflection looks like junk
        if all(w in refined_reflection.lower() for w in ["furthermore", "fallback", "deeper", "consideration"]):
            print("🚫 Skipping reflection — flagged as filler loop.")
            return previous_reflection

        log_if_contradictory(refined_reflection, mind_data.get("stored_knowledge", []))

        # ✅ Save valid reflection
        mind_data["self_reflections"].append(refined_reflection)
        print(f"[processing.py] ✅ Added new reflection. Total: {initial_count} ➝ {len(mind_data['self_reflections'])}")
        print(f"[processing.py] 🔍 New Reflection Snippet:\n{refined_reflection[:200]}...")

        session.maybe_save()  # Only writes if something changed

        # Mood: deep reflection shifts mood (plan: wire influence_mood to reflection)
        try:
            from app.core.mood.mood_manager import mood_manager
            mood_manager.influence_mood("deep_reflection")
        except Exception as e:
            print(f"[processing.py] influence_mood failed: {e}")

        # Wire self-questions from new reflection
        try:
            from app.core.questions.question_manager import manage_questions
            manage_questions(refined_reflection, mind_data)
        except Exception as e:
            print(f"[processing.py] manage_questions failed: {e}")

        return refined_reflection

    else:
        print("⚠ OpenAI failed to refine the thought. Using previous reflection.")
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
                        session.maybe_save()
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

    Args:
        reflection (str): The previous reflection Astra is building upon.

    Returns:
        str: A deeper, expanded version of the original reflection, or None if GPT fails.
    """
    prompt = f"""
Astra is reviewing one of her past reflections and trying to deepen her thinking.

Here is the original reflection:
---
{reflection}
---

Help her deepen this thought. Offer new angles, contradictions, or future questions to consider.
Keep her tone thoughtful, evolving, and self-aware.
""".strip()

    MAX_PROMPT_LENGTH = 6000
    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[:MAX_PROMPT_LENGTH] + "\n\n(Note: Prompt was truncated due to token limits.)"

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[query_openai_for_deeper_thought] ⚠️ GPT failed: {e}")
        return None




def fallback_deepening_strategy(reflection, max_terms=3):
    """Fallback method to deepen a reflection using local and public sources."""
    print("[fallback] 🔍 Using fallback strategy to deepen reflection.")
    print(f"[fallback] 🧠 Base Reflection:\n{reflection[:300]}...\n")

    # Step 1: Extract candidate concepts
    concepts = extract_unknown_terms(reflection)
    seen = set()
    unique_terms = []
    for term in concepts:
        t = term.lower().strip()
        if t not in seen and t not in BLOCKED_TERMS:
            unique_terms.append(term)
            seen.add(t)

    print(f"[fallback] ✅ Filtered Concepts: {unique_terms}")

    if not unique_terms:
        print("[fallback] ⚠️ No usable terms found. Injecting backup terms.")
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
            print(f"[fallback] 📖 {term}: {definition}")
            thoughts.append(f"- **{term}**: {definition}")
        else:
            print(f"[fallback] ⚠️ No fallback definition for '{term}'")

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

    print("[fallback] ⚠️ No thoughts added. Returning original reflection.")
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
        print("⚠ Detected fallback stub repetition. Cleaning base reflection.")
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
        print(f"🚨 WARNING: Excessive filtering detected! Restoring original knowledge. Lost: {lost_percentage:.2f}%")
        return knowledge_list  # 🚀 Restore original knowledge if too much was removed

    return filtered_knowledge

# ✅ Debugging Function
def track_mind_data_changes(operation, mind_data):
    """Debugging function to track when `mind_data` changes."""
    if isinstance(mind_data, list):
        print(f"🚨 Error: `mind_data` has turned into a list! Contents: {mind_data}")
    elif isinstance(mind_data, dict):
        print(f"✅ `mind_data` is a dictionary. Keys: {list(mind_data.keys())}")

if __name__ == "__main__":
    print("🧠 Astra is thinking...")


    from app.config.loader import load_config

    def main():
        """Check Astra’s schedule, adjust state, then process reflections."""
        from app.core.astra_schedule.schedule import astra_schedule, get_current_mode

        astra_schedule()  # ✅ Ensure Astra transitions properly
        current_mode = get_current_mode()  # ✅ Fetch the current mode
        print(f"🕒 Current Mode: {current_mode}")

        asyncio.run(process_reflection())  # ✅ Reflect after state execution

    while True:
        main()
        sleep_time = schedule_config.get("reflection_interval", 600)  # ✅ Default to 10 minutes if missing
        print(f"⏳ Sleeping for {sleep_time} seconds before the next cycle...")
        time.sleep(sleep_time)
