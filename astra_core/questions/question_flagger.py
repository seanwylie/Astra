# In question_flagger.py
from astra_core.config_loader import load_config

# Load configuration files
question_config = load_config("question_config")
# astra_core/questions/question_flagger.py

def flag_unresolved_question(questions, mind_data):
    """Flags a question as unresolved only if Astra truly cannot answer it."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    valid_questions = []

    for question in questions:
        question = question.strip()

        if len(question) < 5:  
            print(f"⚠ Ignoring invalid question: {question}")
            continue

        # 🔥 **Remove the category check to prevent false skips**
        print(f"🔍 Checking if Astra can answer: {question}")

        if can_answer_question(question, mind_data):
            continue  # Skip flagging if answer exists

        print(f"⚠ Flagging unresolved question: {question}")
        unresolved_questions.append({
            "question": question,
            "unresolved": True,
            "context": "Unresolved due to lack of knowledge."
        })

        valid_questions.append(question)

    mind_data["unresolved_questions"] = unresolved_questions
    return valid_questions


def can_answer_question(question, mind_data):
    """Determines if a question can be answered using Astra's stored knowledge as full words, not character by character."""
    
    # Ensure question is a string
    question = str(question).strip().lower()

    # Retrieve stored knowledge as lowercase strings
    stored_knowledge = [str(k).strip().lower() for k in mind_data.get("stored_knowledge", [])]

    # 🔥 Fix: Ensure we compare against FULL stored knowledge phrases, not character-wise
    print(f"🔍 Checking stored knowledge for exact match: {question}")

    # 🔥 Fix: Instead of exact match, allow substrings for more flexible checking
    return any(question in knowledge for knowledge in stored_knowledge)
