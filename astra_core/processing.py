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


def process_reflection():
    """Generate, refine, and deepen Astra's reflections while preventing duplicate deeper thoughts."""
    mind_data = load_mind()

    # print(f"🔍 Debug: Type of `mind_data`: {type(mind_data)}")
    # print(f"🔍 Debug: Raw `mind_data`: {mind_data}")
    # print(f"🔍 Debug: Type of `self_reflections` after load: {type(mind_data['self_reflections'])}")


    # if "self_reflections" in mind_data:
        # print(f"🔍 Debug: Type of `mind_data['self_reflections']`: {type(mind_data['self_reflections'])}")
        # (f"🔍 Debug: Content of `mind_data['self_reflections']`: {mind_data['self_reflections']}")
        # print(f"🔍 Debug: Type of `self_reflections` after load: {type(mind_data['self_reflections'])}")

    # else:
        # print("🚨 `self_reflections` is MISSING from `mind_data`!")

    # ✅ Ensure `mind_data` is properly structured
    if not isinstance(mind_data.get("self_reflections", []), list):
        print("🚨 Error: `self_reflections` is not a list! Resetting...")
        mind_data["self_reflections"] = []

    if not isinstance(mind_data.get("self_questions", []), list):
        print("🚨 Error: `self_questions` is not a list! Resetting...")
        mind_data["self_questions"] = []

    if not isinstance(mind_data.get("stored_knowledge", []), list):
        print("🚨 Error: `stored_knowledge` is not a list! Resetting...")
        mind_data["stored_knowledge"] = []

    # ✅ Generate a new reflection
    new_reflection = generate_reflection(mind_data["stored_knowledge"], mind_data["self_reflections"])
    # print(f"🔍 Debug: Type of `new_reflection`: {type(new_reflection)}")

    # ✅ Expand reflection (deepen thought process)
    # expanded_reflection = deepen_reflection(new_reflection)
    expanded_reflection = new_reflection # Delete me when we get this working
    # print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")

        # ✅ Extract unknown concepts from the deepened reflection
    unknown_concepts = knowledge_manager.extract_unknown_terms(expanded_reflection, mind_data)

    # 🔹 Seek external knowledge if gaps remain
    if unknown_concepts:
        print(f"🌐 Astra detected unknown concepts: {unknown_concepts}")
        mind_data = knowledge_manager.retrieve_external_knowledge(unknown_concepts, mind_data)

    # print(f"🔍 Debug: Type of return value from `retrieve_external_knowledge()`: {type(mind_data)}")


    # ✅ Remove any existing "Deeper Thought" before appending a new one
    expanded_reflection = "\n\n".join(
        line for line in expanded_reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:")
    )

    # print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")
    # print(f"🔍 Debug (Before Error): Type of `mind_data`: {type(mind_data)}")
    # print(f"🔍 Debug (Before Error): Type of `mind_data['self_reflections']`: {type(mind_data.get('self_reflections'))}")

    # ✅ Generate a varied "Deeper Thought"
    deeper_thought_templates = general_config["deeper_thought_templates"]
    deeper_thought = f"\n\n🔍 Deeper Thought: {random.choice(deeper_thought_templates)}"

    # ✅ Append only ONE "Deeper Thought"
    expanded_reflection += deeper_thought

    # Example usage:
    track_mind_data_changes("loading from file", mind_data)

    # print(f"🔍 Debug: Type of `mind_data['self_reflections']`: {type(mind_data['self_reflections'])}")
    # print(f"🔍 Debug: Content of `mind_data['self_reflections']`: {mind_data['self_reflections']}")

    # ✅ Prevent duplicate reflections before adding
    # ✅ Prevent duplicate reflections before adding
    if expanded_reflection not in mind_data["self_reflections"]:

        # print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")
        print(f"🔍 Debug: Value of `expanded_reflection`: {expanded_reflection[:200]}...")  # Print only first 200 chars

        mind_data["self_reflections"].append(expanded_reflection)
        print(f"📝 Added new reflection: {expanded_reflection[:100]}...")

    # ✅ Generate a varied follow-up question
    question_templates = general_config["question_templates"]

    # ✅ Extract a meaningful portion of the reflection for context
    shortened_reflection = expanded_reflection[:150].split(".")[0]  # Grab first sentence if possible

    num_questions = random.randint(1, 3)  # Generate 1-3 questions per cycle
    for _ in range(num_questions):
        new_question = f"{random.choice(question_templates)} ({shortened_reflection}...)"


    # ✅ Ensure `self_questions` is a list
    if not isinstance(mind_data["self_questions"], list):
        print("🚨 Error: `self_questions` is not a list! Resetting...")
        mind_data["self_questions"] = []

    # ✅ Debug print to see generated questions
    print(f"🧐 DEBUG: Generated new question → {new_question}")

# ✅ Extract core question phrase for better duplicate detection
    question_core = new_question.split("(")[0].strip().lower()

# ✅ Prevent duplicate self-questions based on core meaning
    if not any(question_core in q.lower() for q in mind_data["self_questions"]):
        mind_data["self_questions"].append(new_question)
        print(f"✅ DEBUG: Successfully added question → {new_question[:100]}...")
    else:
        print(f"⚠ DEBUG: Skipped duplicate question → {new_question[:100]}...")


    # ✅ Merge and intelligently filter knowledge
    refined_idea = refine_knowledge(mind_data["stored_knowledge"], mind_data)

    # ✅ If the refined idea isn't redundant, add it
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")

    # ✅ Filter duplicates & short entries
    mind_data["stored_knowledge"] = filter_knowledge(mind_data["stored_knowledge"])

    # 🚨 CRITICAL CHECK: Ensure `mind_data` is not empty
    if not mind_data or not isinstance(mind_data, dict):
        print("🚨 [CRITICAL ERROR] processing.py detected an EMPTY mind file before saving!")
    
    # print(f"🔍 Debug: Type of `self_reflections` AFTER appending: {type(mind_data['self_reflections'])}")

    # ✅ Save updated mind file
    save_mind(mind_data)

    return expanded_reflection



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
