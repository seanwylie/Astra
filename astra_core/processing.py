import random
import os
import sys
import asyncio
import time
from openai import OpenAI, RateLimitError
from astra_core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from astra_core.dinner.dinner_journal import log_if_ethically_conflicting, log_if_contradictory
from fuzzywuzzy import fuzz
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import debug_log
from astra_core.config_loader import load_config
from astra_interfaces.smart_mind_session import SmartMindSession


# ✅ Ensure Python knows where to find Astra’s core modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))




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

    previous_reflection = (
        random.choice(reflections[-5:]) if len(reflections) >= 5 else reflections[-1]
    )

    initial_count = len(reflections)
    print(f"[processing.py] 🧠 Last Reflection Before Deepening ({initial_count} total):\n{previous_reflection[:200]}...")

    # 🧠 Attempt to deepen a reflection
    refined_reflection = query_openai_for_deeper_thought(previous_reflection)

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

        return refined_reflection

    else:
        print("⚠ OpenAI failed to refine the thought. Using previous reflection.")
        return previous_reflection


def query_openai_for_deeper_thought(reflection):
    """Ask OpenAI to refine Astra’s reflections, or fallback gracefully if over quota."""
    prompt = f"""
    Astra is an AI that evolves her thoughts over time. She builds on past reflections instead of repeating them.

    Last Reflection:
    "{reflection}"

    Expand on this idea. Provide deeper insight, connect it to knowledge Astra has, or introduce a new perspective.
    """

    try:
        response = OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()

    except RateLimitError as e:
        print(f"⚠️ Hit OpenAI rate limit: {e}")
        time.sleep(10)  # ⏳ Back off before triggering fallback
        return fallback_deepening_strategy(reflection)

    except Exception as e:
        print(f"🚨 OpenAI request failed: {e}")
        return fallback_deepening_strategy(reflection)

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


    from astra_core.config_loader import load_config

    def main():
        """Check Astra’s schedule, adjust state, then process reflections."""
        from astra_core.astra_schedule.schedule import astra_schedule, get_current_mode

        astra_schedule()  # ✅ Ensure Astra transitions properly
        current_mode = get_current_mode()  # ✅ Fetch the current mode
        print(f"🕒 Current Mode: {current_mode}")

        asyncio.run(process_reflection())  # ✅ Reflect after state execution

    while True:
        main()
        sleep_time = schedule_config.get("reflection_interval", 600)  # ✅ Default to 10 minutes if missing
        print(f"⏳ Sleeping for {sleep_time} seconds before the next cycle...")
        time.sleep(sleep_time)
