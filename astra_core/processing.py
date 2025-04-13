import random
import os
import sys
import asyncio
import time
import openai
from astra_core.astra_helpers.utils_helper import extract_unknown_terms, lookup_definition
from fuzzywuzzy import fuzz

# ✅ Ensure Python knows where to find Astra’s core modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config
from astra_core.config_loader import debug_log

# ✅ Load configuration
general_config = load_config("general_config")
schedule_config = load_config("schedule_config")

# ✅ Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])

async def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring memory consistency."""
    debug_log("Loading")  
    mind_data = load_mind()
    validate_mind_structure(mind_data)

    reflections = mind_data.get("self_reflections", [])
    if not reflections:
        print("🤔 I have no reflections yet!")
        return "🤔 I have no reflections yet!"

    # 🔄 Choose a previous reflection randomly if we have a history
    previous_reflection = (
        random.choice(reflections[-5:]) if len(reflections) >= 5 else reflections[-1]
    )

    initial_count = len(reflections)
    print(f"[processing.py] 🧠 Last Reflection Before Deepening ({initial_count} total):\n{previous_reflection[:200]}...")

    # 🔁 Prevent loop traps
    if len(reflections) > 3:
        recent = reflections[-5:]
        last_base = previous_reflection[:100].strip().lower()
        is_looping = False

        print("🔍 [loop check] Comparing last reflection to recent entries:")
        for i, r in enumerate(recent[:-1]):
            compare_base = r[:100].strip().lower()
            ratio = fuzz.partial_ratio(last_base, compare_base)
            print(f"   • Similarity to Reflection {i}: {ratio}%")

            if ratio > 75 or last_base[:60] in compare_base:
                is_looping = True
                print(f"⚠ Detected loop with Reflection {i} (ratio: {ratio}%)")
                break

        if is_looping:
            print("⚠ Reflection topic is repeating. Attempting knowledge expansion instead.")
            refined_knowledge = refine_knowledge(mind_data.get("stored_knowledge", []), mind_data)
            if refined_knowledge:
                print("[processing.py] ✅ Knowledge expansion triggered instead of new reflection.")
                save_mind(mind_data, force=True)
                return refined_knowledge
            else:
                print("⚠ Knowledge expansion failed. Falling back to last reflection.")
                return previous_reflection


    # 🧠 Default: attempt to deepen a reflection
    refined_reflection = query_openai_for_deeper_thought(previous_reflection)
    # refined_reflection = expand_reflection(refined_reflection)

    if refined_reflection:
        mind_data["self_reflections"].append(refined_reflection)
        print(f"[processing.py] ✅ Added new reflection. Total: {initial_count} ➝ {len(mind_data['self_reflections'])}")
        print(f"[processing.py] 🔍 New Reflection Snippet:\n{refined_reflection[:200]}...")
        save_mind(mind_data, force=True)

        return refined_reflection
    else:
        print("⚠ OpenAI failed to refine the thought. Using previous reflection.")
        return previous_reflection




def query_openai_for_deeper_thought(reflection):
    """Ask OpenAI to refine Astra’s reflections, or fallback if over quota."""
    prompt = f"""
    Astra is an AI that evolves her thoughts over time. She builds on past reflections instead of repeating them.

    Last Reflection:
    "{reflection}"

    Expand on this idea. Provide deeper insight, connect it to knowledge Astra has, or introduce a new perspective.
    """

    try:
        response = openai.OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"🚨 OpenAI request failed: {e}")
        return fallback_deepening_strategy(reflection)

    return None

def fallback_deepening_strategy(reflection):
    """Fallback method to deepen a reflection using local and public sources."""
    print("[fallback] 🔍 Using fallback strategy to deepen reflection.")
    print(f"[fallback] 🧠 Base Reflection:\n{reflection[:300]}...\n")

    # Step 1: Extract candidate concepts
    concepts = extract_unknown_terms(reflection)
    print(f"[fallback] 🧠 Extracted Terms: {concepts}")

    # Step 2: Check recent reflections for reused terms
    mind = load_mind()
    recent_reflections = mind.get("self_reflections", [])[-10:]
    recent_text = " ".join(recent_reflections).lower()
    recent_terms = extract_unknown_terms(recent_text)
    recent_terms_set = set(term.lower() for term in recent_terms)
    print(f"[fallback] 🔍 Filtering terms used recently: {sorted(recent_terms_set)}")

    # Step 3: Filter out repeated concepts
    unique_terms = [term for term in concepts if term.lower() not in recent_terms_set]
    print(f"[fallback] ✅ Unique Terms This Round: {unique_terms}")

    # Step 4: Inject novel seeds if nothing is new
    if not unique_terms:
        backup_terms = ["entropy", "identity", "boundaries", "origin", "bias", "perspective", "scale", "truth", "memory", "value"]
        unique_terms = random.sample(backup_terms, 2)
        print(f"[fallback] 🧠 No novel terms found. Injected backup terms: {unique_terms}")

    # Step 5: Lookup definitions for the selected terms
    thoughts = []
    for term in unique_terms:
        definition = lookup_definition(term)
        if definition:
            print(f"[fallback] 📖 Found definition for '{term}': {definition}")
            thoughts.append(f"- **{term}**: {definition}")
        else:
            print(f"[fallback] ⚠️ No definition found for '{term}'.")

    # Step 6: Synthesize a deepening insight if possible
    if thoughts:
        branches = [
            "What contradiction might challenge this idea?",
            "How would someone from another culture interpret this?",
            "What if this perspective is wrong?",
            "What’s the emotional root behind this insight?",
            "Could this be explained through another sense or modality?",
        ]
        deep_question = random.choice(branches)

        enriched = (
            reflection
            + "\n\n🧠 Fallback Deepening:\n"
            + "\n".join(thoughts)
            + f"\n\n🔍 Deeper Consideration: {deep_question}"
        )
        print("[fallback] ✅ Fallback reflection extended. Preview:\n", enriched[:300], "...\n")
        return enriched

    print("[fallback] ⚠ No new knowledge added. Returning original reflection.")
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
