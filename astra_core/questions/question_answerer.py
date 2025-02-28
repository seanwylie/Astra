import sys
import os

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_interfaces`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# astra_core/questions/question_answerer.py
from astra_interfaces.influence import save_mind  # Import save_mind from influence.py
from astra_core.questions.question_flagger import can_answer_question

def self_answer_questions(mind_data):
    """Process Astra's questions and answer them using stored knowledge before flagging unresolved ones."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    unanswered_questions = []

    print(f"Processing {len(mind_data['self_questions'])} self-questions.")

    for question in mind_data["self_questions"]:
        question_text = question["question"]

        # First, try to answer using stored knowledge
        if can_answer_question(question_text, mind_data):  
            print(f"✅ Answered: {question_text}")
            continue  # Skip flagging since it's already answered

        # If not answered, flag it as unresolved
        print(f"⚠ Unresolved: {question_text}")
        unanswered_questions.append(question)

    mind_data["self_questions"] = unanswered_questions
    mind_data["unresolved_questions"] = unresolved_questions

    save_mind(mind_data)
    return unanswered_questions
