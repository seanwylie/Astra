from app.config.loader import load_config
from app.core.questions.question_generator import generate_questions  # Generates raw questions
from app.core.questions.question_utils import filter_questions, categorize_question, generate_category_embeddings
from app.core.questions.question_flagger import flag_unresolved_question
from app.core.questions.question_answerer import self_answer_questions
from app.core.questions.question_tracker import track_question_patterns
from fuzzywuzzy import fuzz  # ✅ Added for fuzzy matching

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")  # Load deeper soul-based questioning parameters
question_config = load_config("question_config")


def deduplicate_questions(questions, threshold=65):  # 🔥 Lower threshold from 85 to 70
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
        # else:
            # print(f"⚠ Near-exact duplicate found. Allowing minor rewording: {question_text}")  # 🔥 Less strict duplicate handling

    return unique_questions



def manage_questions(reflection, mind_data):
    """Manages Astra's question pipeline, ensuring generated questions are stored properly."""
    
    # Step 1: Generate raw questions
    raw_questions, _ = generate_questions(reflection, mind_data)

    # Step 2: Convert raw_questions into list and add to self_questions
    new_questions = [{"question": q} for q in raw_questions.get("general", [])]

    if not new_questions:
        print("⚠ No new questions were generated!")
    else:
        print(f"✅ Adding {len(new_questions)} new questions to self_questions.")

    # 🔥 Fix: Ensure new questions persist
    if "self_questions" not in mind_data or not isinstance(mind_data["self_questions"], list):
        mind_data["self_questions"] = []

    mind_data["self_questions"].extend(new_questions)

    # Step 3: Answer questions FIRST before filtering
    unanswered_questions = self_answer_questions(mind_data)


    # Step 4: Only process unresolved questions from here onward
    filtered_questions = filter_questions(mind_data, unanswered_questions)
    unique_questions = deduplicate_questions(filtered_questions)

    # Step 5: Categorize remaining questions (batch: list of texts + category_embeddings)
    category_embeddings = generate_category_embeddings(question_config)
    question_texts = [q['question'] for q in unique_questions]
    categorized_questions = categorize_question(question_texts, category_embeddings)

    # Step 6: Flag only what cannot be answered
    flagged_questions = flag_unresolved_question([c['question'] for c in categorized_questions], mind_data)

    # Step 7: Track patterns for long-term learning
    track_question_patterns(mind_data)

    # 🔥 Fix: Debug check before final save
    print(f"✅ Final check before saving: {len(mind_data['self_questions'])} questions stored.")

    return flagged_questions


