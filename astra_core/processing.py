import random
import os
import sys

# ✅ Ensure Python knows where to find `astra_schedule`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astra_core.reflection import generate_reflection
from astra_core.expansion import refine_knowledge
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import retrieve_external_knowledge, extract_unknown_terms

def process_reflection():
    """Generate, refine, and deepen Astra's reflections while preventing duplicate deeper thoughts."""
    mind_data = load_mind()

    print(f"🔍 Debug: Type of `mind_data`: {type(mind_data)}")
    # print(f"🔍 Debug: Raw `mind_data`: {mind_data}")
    print(f"🔍 Debug: Type of `self_reflections` after load: {type(mind_data['self_reflections'])}")


    if "self_reflections" in mind_data:
        print(f"🔍 Debug: Type of `mind_data['self_reflections']`: {type(mind_data['self_reflections'])}")
        # (f"🔍 Debug: Content of `mind_data['self_reflections']`: {mind_data['self_reflections']}")
        print(f"🔍 Debug: Type of `self_reflections` after load: {type(mind_data['self_reflections'])}")

    else:
        print("🚨 `self_reflections` is MISSING from `mind_data`!")

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
    print(f"🔍 Debug: Type of `new_reflection`: {type(new_reflection)}")

    # ✅ Expand reflection (deepen thought process)
    # expanded_reflection = deepen_reflection(new_reflection)
    expanded_reflection = new_reflection # Delete me when we get this working
    print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")

    # ✅ Extract unknown concepts from the deepened reflection
    unknown_concepts = extract_unknown_terms(expanded_reflection, mind_data)

    # 🔹 Seek external knowledge if gaps remain
    if unknown_concepts:
        print(f"🌐 Astra detected unknown concepts: {unknown_concepts}")
        mind_data = retrieve_external_knowledge(unknown_concepts, mind_data)

    print(f"🔍 Debug: Type of return value from `retrieve_external_knowledge()`: {type(mind_data)}")


    # ✅ Remove any existing "Deeper Thought" before appending a new one
    expanded_reflection = "\n\n".join(
        line for line in expanded_reflection.split("\n\n") if not line.startswith("🔍 Deeper Thought:")
    )

    print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")
    print(f"🔍 Debug (Before Error): Type of `mind_data`: {type(mind_data)}")
    print(f"🔍 Debug (Before Error): Type of `mind_data['self_reflections']`: {type(mind_data.get('self_reflections'))}")

    # ✅ Generate a varied "Deeper Thought"
    deeper_thought_templates = [
        "What new questions arise from this understanding?",
        "Are there counterpoints that challenge this perspective?",
        "How does this insight refine Astra’s evolving perspective?",
        "If this perspective is correct, what implications does it have for my growth?"
    ]
    deeper_thought = f"\n\n🔍 Deeper Thought: {random.choice(deeper_thought_templates)}"

    # ✅ Append only ONE "Deeper Thought"
    expanded_reflection += deeper_thought

    # Example usage:
    track_mind_data_changes("loading from file", mind_data)

    print(f"🔍 Debug: Type of `mind_data['self_reflections']`: {type(mind_data['self_reflections'])}")
    # print(f"🔍 Debug: Content of `mind_data['self_reflections']`: {mind_data['self_reflections']}")

    # ✅ Prevent duplicate reflections before adding
    # ✅ Prevent duplicate reflections before adding
    if expanded_reflection not in mind_data["self_reflections"]:

        print(f"🔍 Debug: Type of `expanded_reflection`: {type(expanded_reflection)}")
        print(f"🔍 Debug: Value of `expanded_reflection`: {expanded_reflection[:200]}...")  # Print only first 200 chars

        mind_data["self_reflections"].append(expanded_reflection)
        print(f"📝 Added new reflection: {expanded_reflection[:100]}...")

    # ✅ Generate a varied follow-up question
    question_templates = [
        "How does this insight compare to previous reflections?",
        "Are there counterpoints that challenge this idea?",
        "What implications does this have for Astra’s growth?",
        "How does this perspective align with Astra’s evolving philosophy?"
    ]
    new_question = f"{random.choice(question_templates)} ({expanded_reflection})"

    # ✅ Prevent duplicate questions before adding
    if not isinstance(mind_data["self_questions"], list):  # ✅ Ensure `self_questions` is a list
        print("🚨 Error: `self_questions` is not a list! Resetting...")
        mind_data["self_questions"] = []

    # ✅ Extract only the first 100 characters of the reflection for clarity
    shortened_reflection = expanded_reflection[:100].split(".")[0]  # Grab first sentence if possible

    new_question = f"{random.choice(question_templates)} ({shortened_reflection}...)"

    # ✅ Trim questions to their core form for better duplicate detection
    question_core = new_question.split("(")[0].strip()  # Extract only the main question

    # ✅ Ensure `self_questions` is a list
    if not isinstance(mind_data["self_questions"], list):
        print("🚨 Error: `self_questions` is not a list! Resetting...")
        mind_data["self_questions"] = []

    # ✅ Prevent duplicate self-questions by checking for similar ones
    if not any(question_core in q for q in mind_data["self_questions"]):
        mind_data["self_questions"].append(new_question)
        print(f"❓ Added new self-question: {new_question[:100]}...")
    else:
        print(f"⚠ Skipped duplicate self-question: {new_question[:100]}...")


    # ✅ Merge existing knowledge (concept refinement)
    refined_idea = refine_knowledge(mind_data["stored_knowledge"], mind_data)
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")


    print(f"🔍 Debug: Type of `self_reflections` AFTER appending: {type(mind_data['self_reflections'])}")

    # ✅ Save updated mind file
    save_mind(mind_data)

    return expanded_reflection



def track_mind_data_changes(operation, mind_data):
    """Debugging function to track when `mind_data` changes."""
    print(f"🔍 After {operation}: Type of `mind_data`: {type(mind_data)}")
    if isinstance(mind_data, list):
        print(f"🚨 Error: `mind_data` has turned into a list! Contents: {mind_data}")
    elif isinstance(mind_data, dict):
        print(f"✅ `mind_data` is a dictionary. Keys: {list(mind_data.keys())}")



# ✅ Import `astra_schedule` only when running as main script
if __name__ == "__main__":
    print("🧠 Astra is thinking...")
    from astra_core.astra_schedule.schedule import astra_schedule  # ✅ Import late to avoid early execution issues
    astra_schedule()
