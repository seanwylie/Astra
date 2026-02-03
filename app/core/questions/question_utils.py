from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer, util
from app.config.loader import load_config
from app.logging_config import get_logger

# Load question config
question_config = load_config("question_config")

# Ensure 'question_categories' exists in the config
if "question_categories" not in question_config:
    raise KeyError("🚨 'question_categories' not found in the config!")

# ✅ Initialize Sentence-BERT model **only once**
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# ✅ Lazily loaded category embeddings
category_embeddings = None

logger = get_logger("questions.utils")

def generate_category_embeddings(question_config):
    """Generate embeddings for each category's sample questions."""
    category_embeddings = {}

    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    for category, details in question_config["question_categories"].items():
        sample_questions = details.get("sample_questions", [])
        if not sample_questions:
            logger.warning("⚠ Warning: No sample questions found for category '%s'", category)
        else:
            category_embeddings[category] = model.encode(sample_questions, convert_to_tensor=True)

    return category_embeddings


def categorize_question(questions, category_embeddings):
    """Categorize a list of questions, ensuring valid output format."""
    categorized_questions = []

    if not isinstance(questions, list):
        logger.warning("⚠ Invalid question format received (not a list): %s", questions)
        return []

    for question in questions:
        if not isinstance(question, str) or len(question) < 5:  # ✅ Ignore short/invalid inputs
            logger.debug("⚠ Skipping invalid question format: %s", question)
            continue
        
        question_embedding = model.encode(question, convert_to_tensor=True)

        # Compare the question with all category embeddings using cosine similarity
        similarities = {
            category: util.pytorch_cos_sim(question_embedding, embeddings).mean().item()
            for category, embeddings in category_embeddings.items()
        }

        if not similarities:  # ✅ Handle empty case
            logger.debug("⚠ Warning: No similarities found for '%s'", question)
            continue

        best_category = max(similarities, key=similarities.get)

        logger.debug("🔍 Categorized '%s' as '%s'", question, best_category)

        # ✅ Append full question instead of a nested list
        categorized_questions.append({"question": question, "category": best_category})

    return categorized_questions  # ✅ Ensures a flat list of dictionaries
    # return questions


def filter_questions(mind_data, new_questions):
    """Filters out duplicate, near-duplicate, or answered questions before storing."""
    logger.debug("🔍 filter_questions() received %s questions", len(new_questions))

    if not new_questions:
        logger.debug("⚠ No new questions received, stopping filtering early!")
        return []

    filtered_questions = []
    stored_knowledge_set = set(mind_data.get("stored_knowledge", []))  # ✅ Prevents mutation

    # ✅ Store existing questions with precomputed lowercase versions
    existing_questions = {
        q["question"].strip().lower(): q
        for q in mind_data.get("self_questions", []) if isinstance(q, dict) and "question" in q
    }

    for question_entry in new_questions:
        if isinstance(question_entry, dict) and "question" in question_entry:
            question_text = question_entry["question"].strip()
        else:
            logger.debug("⚠ Unexpected question format (missing 'question'): %s", question_entry)
            continue  # Skip invalid entries

        if not question_text or len(question_text) < 6:
            logger.debug("⚠ Ignoring invalid question (too short or empty): %s", question_text)
            continue

        question_text_lower = question_text.lower()

        # ✅ Reject dictionary definitions explicitly before filtering
        if question_text_lower in stored_knowledge_set and not question_text_lower.startswith("📖"):
            logger.debug("⚠ Possible false positive → Skipping '%s' (already in stored knowledge)", question_text)
            continue  # 🚨 Prevents accidentally removing legitimate questions!

        is_duplicate = any(fuzz.ratio(question_text_lower, existing_text) > 65 for existing_text in existing_questions)

        if not is_duplicate:
            filtered_questions.append(question_entry)
            logger.debug("✅ Accepted New Question: %s", question_text)

    logger.debug("🔍 %s questions passed filtering and will be added.", len(filtered_questions))

    return filtered_questions
