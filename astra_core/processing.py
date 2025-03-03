import random
import os
import sys
from fuzzywuzzy import fuzz  # ✅ Re-added missing fuzzy matching import

# ✅ Ensure Python knows where to find `astra_schedule`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.knowledge import knowledge_manager
from astra_core.reflection import generate_reflection
from astra_core.questions.question_manager import generate_questions, track_question_patterns
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config  # ✅ Load configs dynamically
from astra_core.questions.question_manager import manage_questions


general_config = load_config("general_config")  # ✅ Load general settings


# ✅ Function: Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])


def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring questions are generated & answered."""
    mind_data = load_mind()
    validate_mind_structure(mind_data)

    # ✅ Generate & expand reflection
    new_reflection = generate_reflection(mind_data["stored_knowledge"], mind_data["self_reflections"])
    expanded_reflection = expand_reflection(new_reflection)

    # 🔍 **Extract unknown terms before generating questions**
    unknown_terms = knowledge_manager.extract_unknown_terms(expanded_reflection)
    if unknown_terms:
        print(f"🔍 Detected unknown terms: {unknown_terms}")
        found_new_knowledge = knowledge_manager.retrieve_external_knowledge(unknown_terms)
        if found_new_knowledge:
            print(f"✅ New knowledge added from external lookup: {unknown_terms}")

    # ✅ Store reflection if it's new
    if expanded_reflection not in mind_data["self_reflections"]:
        mind_data["self_reflections"].append(expanded_reflection)
        print(f"📝 Added new reflection: {expanded_reflection[:100]}...")

    # ✅ Generate new questions using Astra's enhanced system
    categorized_questions, category_counts = generate_questions(expanded_reflection, mind_data)
    print(f"🔍 Debug: Generated categorized_questions: {categorized_questions}")

    new_questions = []
    for category, questions in categorized_questions.items():
        if isinstance(questions, list):
            new_questions.extend(questions)

    print(f"🔍 Debug: Extracted new questions before filtering: {new_questions}")

    mind_data["self_questions"].extend(new_questions)

    # ✅ Merge knowledge & filter
    refined_idea = refine_knowledge(mind_data["stored_knowledge"], mind_data)
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")

    print(f"🔍 Before filtering, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    # filtered_knowledge = filter_knowledge(mind_data["stored_knowledge"])
    # mind_data["stored_knowledge"] = list(set(mind_data["stored_knowledge"]) | set(filtered_knowledge))

    print(f"🔍 After filtering, stored knowledge count: {len(mind_data['stored_knowledge'])}")

    save_mind(mind_data)
    return expanded_reflection


def expand_reflection(reflection):
    """Deepens thoughts and ensures unique reflections."""
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
        if len(entry) < 5:  # Ignore tiny junk entries
            continue

        key = entry.lower().strip()

        # ✅ Only remove near-duplicates if the similarity is **very high** (>85%)
        if any(fuzz.ratio(key, existing) > 85 for existing in seen):
            print(f"⚠ [FILTERED] Removing near-duplicate knowledge: {entry[:100]}")
            continue  # Avoid near-duplicates but allow slight variations

        seen.add(key)
        filtered_knowledge.append(entry)

    return filtered_knowledge




# ✅ Debugging Function
def track_mind_data_changes(operation, mind_data):
    """Debugging function to track when `mind_data` changes."""
    if isinstance(mind_data, list):
        print(f"🚨 Error: `mind_data` has turned into a list! Contents: {mind_data}")
    elif isinstance(mind_data, dict):
        print(f"✅ `mind_data` is a dictionary. Keys: {list(mind_data.keys())}")


# ✅ Import `astra_schedule` only when running as main script
if __name__ == "__main__":
    print("🧠 Astra is thinking...")
    from astra_core.astra_schedule.schedule import astra_schedule  # ✅ Import late to avoid early execution issues
    astra_schedule()