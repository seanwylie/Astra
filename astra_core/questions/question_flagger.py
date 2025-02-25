# In question_flagger.py

def flag_unresolved_question(question, mind_data):
    """Flags a question as unresolved if it cannot be answered using Astra's knowledge."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    
    # If the question can be answered, don't flag it
    if can_answer_question(question, mind_data):
        return False  # Question can be answered, no need to flag
    
    # Flag the question as unresolved and store it as a dictionary
    unresolved_questions.append({
        "question": question,
        "unresolved": True,
        "context": "Unresolved due to lack of knowledge at the moment."
    })
    
    mind_data["unresolved_questions"] = unresolved_questions
    return True  # Flag as unresolved



def can_answer_question(question, mind_data):
    """Determines if a question can be answered using Astra's stored knowledge."""
    stored_knowledge = [k.lower() for k in mind_data.get("stored_knowledge", [])]
    
    # Debugging: Check if the question exists in the stored knowledge
    print(f"Checking stored knowledge for the question: {question}")
    
    return any(question.lower() in knowledge for knowledge in stored_knowledge)
