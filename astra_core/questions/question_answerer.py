import sys
import os

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_interfaces`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# astra_core/questions/question_answerer.py
from astra_interfaces.influence import save_mind  # Import save_mind from influence.py
from astra_core.questions.question_flagger import can_answer_question

def self_answer_questions(mind_data):
    """Process Astra's questions, answering them if possible, and storing both answered and unanswered ones."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    answered_questions = []
    unanswered_questions = []

    print(f"Processing {len(mind_data['self_questions'])} self-questions.")

    for question in mind_data["self_questions"]:
        question_text = question["question"]

        if can_answer_question(question_text, mind_data):  
            print(f"✅ Answered: {question_text}")
            answered_questions.append(question)  # 🔥 Keep answered questions
        else:
            print(f"⚠ Unresolved: {question_text}")
            unanswered_questions.append(question)

    # 🔥 Fix: Ensure `self_questions` is not cleared
    if answered_questions or unanswered_questions:
        mind_data["self_questions"] = answered_questions + unanswered_questions
    else:
        print("🚨 WARNING: No questions left in self_questions before saving!")

    mind_data["unresolved_questions"] = unresolved_questions
    save_mind(mind_data)
    return unanswered_questions
