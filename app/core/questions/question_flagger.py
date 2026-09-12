# In question_flagger.py
from app.config.loader import load_config
from fuzzywuzzy import fuzz

# Load configuration files
question_config = load_config("question_config")


def flag_unresolved_question(questions, mind_data):
    """Store questions that are not yet answered as unresolved."""
    unresolved_questions = list(mind_data.get("unresolved_questions", []))
    valid_questions = []

    for question in questions:
        question = question.strip()

        if len(question) < 5:
            print(f"⚠ Ignoring invalid question: {question}")
            continue

        # Only add if not already answerable
        if not can_answer_question(question, mind_data):
            unresolved_questions.append({
                "question": question,
                "unresolved": True,
                "context": "Stored for future answering."
            })
        valid_questions.append(question)

    mind_data["unresolved_questions"] = unresolved_questions
    return valid_questions


def can_answer_question(question: str, mind_data: dict) -> bool:
    """Return True if this question has been resolved (answer stored in self_questions)."""
    question_clean = question.strip().lower()
    if len(question_clean) < 5:
        return False
    
    # Optimize: Only check answered questions (skip unresolved ones)
    self_questions = mind_data.get("self_questions", [])
    answered_questions = [
        q for q in self_questions 
        if isinstance(q, dict) and not q.get("unresolved", True) and q.get("answer")
    ]
    
    # Optimize: Limit checks to recent answered questions
    MAX_ANSWERED_CHECKS = 50
    recent_answered = answered_questions[-MAX_ANSWERED_CHECKS:] if len(answered_questions) > MAX_ANSWERED_CHECKS else answered_questions
    
    for q in recent_answered:
        q_text = (q.get("question") or "").strip().lower()
        if q_text and fuzz.ratio(question_clean[:200], q_text[:200]) >= 70:
            return True
    return False

