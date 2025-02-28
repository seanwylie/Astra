# In question_flagger.py

def flag_unresolved_question(question, mind_data):
    """Flags a question as unresolved if it cannot be answered using Astra's knowledge."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    
    # Ensure question is a string before processing
    question = ''.join(question) if isinstance(question, list) else str(question)
    
    # If the question can be answered, don't flag it
    if can_answer_question(question, mind_data):
        return [], {}  # ✅ Always return a tuple

    
    # Flag the question as unresolved and store it as a dictionary
    unresolved_questions.append({
        "question": question,
        "unresolved": True,
        "context": "Unresolved due to lack of knowledge at the moment."
    })
    
    mind_data["unresolved_questions"] = unresolved_questions
    
    return [q['question'].strip() if isinstance(q, dict) and 'question' in q else str(q).strip() for q in unresolved_questions]


def can_answer_question(question, mind_data):
    """Determines if a question can be answered using Astra's stored knowledge."""
    stored_knowledge = [str(k).lower() for k in mind_data.get("stored_knowledge", [])]
    
    # Ensure question is a string before processing
    question = str(question) if not isinstance(question, str) else question
    
    # Debugging: Check if the question exists in the stored knowledge
    print(f"Checking stored knowledge for the question: {''.join(question) if isinstance(question, list) else question}")
    
    return any(str(question).lower() in str(knowledge) for knowledge in stored_knowledge)
