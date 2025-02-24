import random
import os
import sys

# ✅ Ensure Python knows where to find `astra_schedule`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.knowledge import knowledge_manager
from astra_core.reflection import generate_reflection
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config  # ✅ Load configs dynamically

general_config = load_config("general_config")  # ✅ Load schedule settings


# ✅ Function: Ensure Mind Structure
def validate_mind_structure(mind_data):
    """Ensure `mind_data` has the correct structure."""
    if not isinstance(mind_data.get("self_reflections", []), list):
        mind_data["self_reflections"] = []

    if not isinstance(mind_data.get("self_questions", []), list):
        mind_data["self_questions"] = []

    if not isinstance(mind_data.get("stored_knowledge", []), list):
        mind_data["stored_knowledge"] = []


# ✅ Function: Process Reflection
def process_reflection():
    """Generate, refine, and deepen Astra's reflections while ensuring questions are generated & answered."""
    mind_data = load_mind()
    validate_mind_structure(mind_data)

    # ✅ Generate & expand reflection
    new_reflection = generate_reflection(mind_data["stored_knowledge"], mind_data["self_reflections"])
    expanded_reflection = expand_reflection(new_reflection)

    # ✅ Store reflection if it's new
    if expanded_reflection not in mind_data["self_reflections"]:
        mind_data["self_reflections"].append(expanded_reflection)
        print(f"📝 Added new reflection: {expanded_reflection[:100]}...")

    # ✅ Extract unknown concepts & seek external knowledge
    unknown_concepts = knowledge_manager.extract_unknown_terms(expanded_reflection, mind_data)
    if unknown_concepts:
        print(f"🌐 Astra detected unknown concepts: {unknown_concepts}")
        mind_data = knowledge_manager.retrieve_external_knowledge(unknown_concepts, mind_data)

    # ✅ Generate & answer questions
    new_questions = generate_questions(expanded_reflection)
    unanswered_questions = answer_questions(mind_data, new_questions)
    mind_data["self_questions"].extend(unanswered_questions)

    # ✅ Merge knowledge & filter
    refined_idea = refine_knowledge(mind_data["stored_knowledge"], mind_data)
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")

    mind_data["stored_knowledge"] = filter_knowledge(mind_data["stored_knowledge"])

    # ✅ Debugging: Track changes before saving
    track_mind_data_changes("before saving", mind_data)

    # ✅ Save updated mind
    save_mind(mind_data)

    return expanded_reflection


# ✅ Function: Expand Reflection
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


# ✅ Function: Generate More Questions
def generate_questions(reflection):
    """Generates multiple unique questions based on the given reflection."""
    question_templates = general_config["question_templates"]
    num_questions = random.randint(2, 5)  # ✅ Increase question output

    shortened_reflection = reflection[:150].split(".")[0]  # Extract key idea
    new_questions = [f"{random.choice(question_templates)} ({shortened_reflection}...)" for _ in range(num_questions)]

    return new_questions


# ✅ Function: Answer Questions Before Storing Them
def answer_questions(mind_data, questions):
    """Checks if questions can be answered from stored knowledge before saving them."""
    unanswered_questions = []

    for question in questions:
        question_core = question.split("(")[0].strip().lower()

        # ✅ If answer exists, archive the question instead of saving it
        if any(question_core in knowledge.lower() for knowledge in mind_data["stored_knowledge"]):
            print(f"✅ Answer found! Archiving question: {question}")
            continue  

        # ✅ Prevent duplicates
        if any(question_core in q.lower() for q in mind_data["self_questions"]):
            print(f"⚠ Duplicate question skipped: {question}")
            continue 

        unanswered_questions.append(question)
        print(f"🧐 New Question Added: {question}")

    return unanswered_questions


# ✅ Function: Filter Knowledge & Remove Duplicates
def filter_knowledge(knowledge_list):
    """Ensure Astra keeps valuable knowledge while avoiding duplicates."""
    filtered_knowledge = []
    seen = set()

    for entry in knowledge_list:
        if len(entry) < 5:  # Ignore tiny junk entries
            continue

        key = entry.lower().strip()

        if key in seen:
            continue  # Avoid duplicates

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
