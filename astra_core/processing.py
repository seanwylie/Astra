from astra_core.reflection import generate_reflection
from astra_core.expansion import refine_knowledge, deepen_reflection
from astra_interfaces.influence import load_mind, save_mind, store_knowledge

import random

def process_reflection():
    """Generate, refine, and deepen Astra's reflections."""
    mind_data = load_mind()

    # ✅ Generate a new reflection
    new_reflection = generate_reflection(mind_data.get("stored_knowledge", []), mind_data.get("self_reflections", []))

    # ✅ Expand reflection (deepen thought process)
    expanded_reflection = deepen_reflection(new_reflection)

    # ✅ Prevent duplicate reflections before adding
    if expanded_reflection not in mind_data["self_reflections"]:
        mind_data["self_reflections"].append(expanded_reflection)
        print(f"📝 Added new reflection: {expanded_reflection[:100]}...")

    # 🔹 Generate a varied follow-up question
    question_templates = [
        "How does this insight compare to previous reflections?",
        "Are there counterpoints that challenge this idea?",
        "What implications does this have for Astra’s growth?",
        "How does this perspective align with Astra’s evolving philosophy?"
    ]
    new_question = f"{random.choice(question_templates)} ({expanded_reflection})"

    # ✅ Prevent duplicate questions before adding
    if new_question not in mind_data["self_questions"]:
        mind_data["self_questions"].append(new_question)
        print(f"❓ Added new self-question: {new_question[:150]}...")

    # ✅ Merge existing knowledge (concept refinement)
    refined_idea = refine_knowledge(mind_data.get("stored_knowledge", []))
    if refined_idea and refined_idea not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(refined_idea)
        print(f"🔹 Refined knowledge added: {refined_idea[:150]}...")

    # ✅ Save updated mind file
    save_mind(mind_data)

    return expanded_reflection



if __name__ == "__main__":
    print("🧠 Astra is thinking...")
    print(process_reflection())
