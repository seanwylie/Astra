import sys
import os
from astra_core.config_loader import debug_log

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_interfaces`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# astra_core/questions/question_answerer.py
from astra_interfaces.influence import save_mind  # Import save_mind from influence.py

def self_answer_questions(mind_data):
    """Store all questions as unresolved without attempting to answer them."""

    unresolved_questions = mind_data.get("unresolved_questions", [])
    new_questions = []

    print(f"Processing {len(mind_data['self_questions'])} self-questions.")

    for question in mind_data["self_questions"]:
        if isinstance(question, str):  
            question_text = question  # ✅ Handle old format
        elif isinstance(question, dict) and "question" in question:
            question_text = question["question"]
        else:
            print(f"⚠ Skipping invalid question format: {question}")  # ✅ Debugging Output
            continue  # Skip corrupted entries

        # 🔥 No answering—just store questions properly
        new_questions.append({
            "question": question_text,
            "unresolved": True,
            "context": "Stored for future answering."
        })

    # 🔥 Fix: Ensure `self_questions` retains all questions without clearing them
    mind_data["self_questions"] = new_questions
    mind_data["unresolved_questions"] = unresolved_questions  # ✅ Keep track of unresolved

    debug_log("Saving")
    save_mind(mind_data)
    return new_questions  # ✅ Return, but no processing
