import sys
import os
import random
from astra_core.config_loader import load_config
from astra_core.questions.question_generator import generate_questions  # Generates raw questions
from astra_core.questions.question_utils import filter_questions, categorize_question
from astra_core.questions.question_flagger import flag_unresolved_question
from astra_core.questions.question_answerer import self_answer_questions
from astra_core.questions.question_tracker import track_question_patterns
from fuzzywuzzy import fuzz  # ✅ Added for fuzzy matching

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")  # Load deeper soul-based questioning parameters
question_config = load_config("question_config")


def deduplicate_questions(questions, threshold=85):
    """Removes near-duplicate questions using fuzzy matching."""
    unique_questions = []
    seen_questions = set()

    for question in questions:
        question_text = question["question"] if isinstance(question, dict) else str(question).strip()
        
        # Check if question is similar to any existing one
        is_duplicate = any(fuzz.ratio(question_text.lower(), existing.lower()) > threshold for existing in seen_questions)

        if not is_duplicate:
            unique_questions.append(question)
            seen_questions.add(question_text.lower())
        else:
            print(f"⚠ Removed duplicate question: {question_text}")

    return unique_questions


def manage_questions(reflection, mind_data):
    """Manages Astra's question pipeline, ensuring answering happens before categorization."""
    
    # Step 1: Generate raw questions
    raw_questions, _ = generate_questions(reflection, mind_data)  # Fix: Capture generated questions
    
    # Step 2: Add generated questions to mind_data
    mind_data["self_questions"].extend([{"question": q} for q in raw_questions.get("general", [])])
    
    # Step 3: Answer questions FIRST before filtering
    unanswered_questions = self_answer_questions(mind_data)

    # Step 4: Only process unresolved questions from here onward
    filtered_questions = filter_questions(mind_data, unanswered_questions)
    unique_questions = deduplicate_questions(filtered_questions)

    # Step 5: Categorize remaining questions
    categorized_questions = {q: categorize_question(q['question']) for q in unique_questions}
    
    # Step 6: Flag only what cannot be answered
    flagged_questions = flag_unresolved_question([q['question'] for q in categorized_questions], mind_data)
    
    # Step 7: Track patterns for long-term learning
    track_question_patterns(mind_data)
    
    return flagged_questions

