# In question_flagger.py
from astra_core.config_loader import load_config

# Load configuration files
question_config = load_config("question_config")
# astra_core/questions/question_flagger.py

def flag_unresolved_question(questions, mind_data):
    """Store all questions as unresolved without checking for answers."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    valid_questions = []

    for question in questions:
        question = question.strip()

        if len(question) < 5:  
            print(f"⚠ Ignoring invalid question: {question}")
            continue

        # 🔥 No checking—just store questions
        unresolved_questions.append({
            "question": question,
            "unresolved": True,
            "context": "Stored for future answering."
        })

        valid_questions.append(question)

    mind_data["unresolved_questions"] = unresolved_questions
    return valid_questions  # ✅ Questions are stored but not processed



def can_answer_question(question, mind_data):
    """Disable question answering; store all questions instead."""
    return False  # ✅ Always store, never answer

