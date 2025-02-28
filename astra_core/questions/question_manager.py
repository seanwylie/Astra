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
    """Manages Astra's question pipeline in a fully modular way."""
    
    # Step 1: Generate raw questions
    raw_questions = generate_questions(reflection, mind_data)
    
    # Step 2: Filter out duplicates and answered questions
    filtered_questions = filter_questions(mind_data, raw_questions)
    
    # Step 3: Deduplicate remaining questions
    unique_questions = deduplicate_questions(filtered_questions)
    
    # Step 4: Self-answer any questions that Astra already knows
    unanswered_questions = self_answer_questions(unique_questions, mind_data)
    
    # Step 5: Categorize questions into themes
    categorized_questions = {q: categorize_question(q['question']) for q in unanswered_questions}
    
    # Step 6: Flag unresolved questions for future learning
    flagged_questions = flag_unresolved_question([q['question'] if isinstance(q, dict) else str(q) for q in categorized_questions], mind_data)
    
    # Step 7: Track question patterns for Astra's long-term learning
    track_question_patterns(mind_data)
    
    return flagged_questions
