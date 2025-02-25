import sys
import os

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_interfaces`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# astra_core/questions/question_answerer.py
from astra_interfaces.influence import save_mind  # Import save_mind from influence.py
from astra_core.questions.question_flagger import flag_unresolved_question


def self_answer_question(mind_data):
    """Process Astra's questions and flag any unresolved ones."""
    unresolved_questions = mind_data.get("unresolved_questions", [])
    unanswered_questions = []  # Keep track of unanswered but not removed questions

    # Debugging: Print current self_questions
    print(f"Processing {len(mind_data['self_questions'])} self-questions.")
    
    # Answering logic...
    for question in mind_data["self_questions"]:
        print(f"Checking question: {question['question']}")
        
        # Flag unresolved questions (check if they can be answered)
        if flag_unresolved_question(question["question"], mind_data):
            print(f"Question is unresolved: {question['question']}")
            unanswered_questions.append(question)
        else:
            print(f"Question resolved: {question['question']}")  # Here, you could add logic to answer the question
            # For now, we mark it as answered (this can be refined to actually provide an answer)
    
    # Update the mind_data with unresolved and unanswered questions
    mind_data["self_questions"] = unanswered_questions  # Keep unresolved in the same list
    mind_data["unresolved_questions"] = unresolved_questions  # Track unresolved separately

    # Save the updated mind data
    save_mind(mind_data)
    
    # Return unanswered questions for further processing or review
    return unanswered_questions
