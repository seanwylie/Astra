import random
import os
import sys

# ✅ Ensure Python knows where to find `astra_schedule`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.reflection import generate_reflection
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import retrieve_external_knowledge, extract_unknown_terms

from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings


import random
from astra_interfaces.influence import load_mind, save_mind, store_knowledge
from astra_core.reflection import generate_reflection
from astra_core.expansion import refine_knowledge
from astra_core.knowledge import retrieve_external_knowledge, extract_unknown_terms
from astra_core.config_loader import load_config

general_config = load_config("general_config")

# ✅ Limit Reflection History to Reduce Repetitive Ideas
MAX_REFLECTION_HISTORY = 2

# ✅ Store Knowledge Every 3 Reflections
REFLECTIONS_BEFORE_KNOWLEDGE = 3

def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring diverse insights and structured knowledge storage."""
    mind_data = load_mind()

    # ✅ Ensure mind data structure is correct
    for key in ["self_reflections", "self_questions", "stored_knowledge"]:
        if not isinstance(mind_data.get(key, []), list):
            print(f"🚨 Error: `{key}` is not a list! Resetting...")
            mind_data[key] = []

    # ✅ Generate a reflection using limited past thoughts
    recent_reflections = mind_data["self_reflections"][-MAX_REFLECTION_HISTORY:]
    new_reflection = generate_reflection(mind_data["stored_knowledge"], recent_reflections)

    # ✅ Ensure new reflection is unique before adding it
    if new_reflection not in mind_data["self_reflections"]:
        print(f"📝 Added new reflection: {new_reflection[:100]}...")
        mind_data["self_reflections"].append(new_reflection)

    # ✅ Extract unknown concepts from the reflection
    unknown_concepts = extract_unknown_terms(new_reflection, mind_data)

    # 🔹 Retrieve external knowledge if necessary
    if unknown_concepts:
        print(f"🌐 Astra detected unknown concepts: {unknown_concepts}")
        mind_data = retrieve_external_knowledge(unknown_concepts, mind_data)

    # ✅ Remove duplicate "Deeper Thought" before adding a new one
    new_reflection = "\n\n".join(
        line for line in new_reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:")
    )

    # ✅ Generate a varied "Deeper Thought"
    deeper_thought_templates = general_config["deeper_thought_templates"]
    deeper_thought = f"\n\n🔍 Deeper Thought: {random.choice(deeper_thought_templates)}"
    new_reflection += deeper_thought

    # ✅ Generate a varied follow-up question
    question_templates = general_config["question_templates"]
    shortened_reflection = new_reflection[:100].split(".")[0]  # Grab first sentence if possible
    new_question = f"{random.choice(question_templates)} ({shortened_reflection}...)"

    # ✅ Prevent duplicate self-questions
    question_core = new_question.split("(")[0].strip()
    if not any(question_core in q for q in mind_data["self_questions"]):
        mind_data["self_questions"].append(new_question)
        print(f"❓ Added new self-question: {new_question[:100]}...")
    else:
        print(f"⚠ Skipped duplicate self-question: {new_question[:100]}...")

    # ✅ Merge existing knowledge
    refined_idea = refine_knowledge(mind_data["stored_knowledge"], mind_data)
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")

    # ✅ Ensure knowledge storage every 3 reflections
    if len(mind_data["self_reflections"]) % REFLECTIONS_BEFORE_KNOWLEDGE == 0:
        knowledge_entry = " ".join(mind_data["self_reflections"][-REFLECTIONS_BEFORE_KNOWLEDGE:])
        store_knowledge(mind_data, knowledge_entry)
        print(f"🧠 Stored New Knowledge: {knowledge_entry[:100]}...")

    # ✅ Save updated mind data
    save_mind(mind_data)

    return new_reflection


def track_mind_data_changes(operation, mind_data):  
    """Debugging function to track when `mind_data` changes."""
    # print(f"🔍 After {operation}: Type of `mind_data`: {type(mind_data)}")
    if isinstance(mind_data, list):
        print(f"🚨 Error: `mind_data` has turned into a list! Contents: {mind_data}")
    elif isinstance(mind_data, dict):
        print(f"✅ `mind_data` is a dictionary. Keys: {list(mind_data.keys())}")



# ✅ Import `astra_schedule` only when running as main script
if __name__ == "__main__":
    print("🧠 Astra is thinking...")
    from astra_core.astra_schedule.schedule import astra_schedule  # ✅ Import late to avoid early execution issues
    astra_schedule()
