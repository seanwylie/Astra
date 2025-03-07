import random
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer, util
from astra_core.config_loader import load_config

# Load question config
question_config = load_config("question_config")

# Ensure 'question_categories' exists in the config
if "question_categories" not in question_config:
    raise KeyError("🚨 'question_categories' not found in the config!")

# ✅ Initialize Sentence-BERT model **only once**
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# ✅ Lazily loaded category embeddings
category_embeddings = None  

def generate_category_embeddings(question_config):
    """Generate embeddings for each category's sample questions."""
    category_embeddings = {}

    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    for category, details in question_config["question_categories"].items():
        sample_questions = details.get("sample_questions", [])
        if not sample_questions:
            print(f"⚠ Warning: No sample questions found for category '{category}'")
        else:
            category_embeddings[category] = model.encode(sample_questions, convert_to_tensor=True)

    return category_embeddings


def categorize_question(questions, category_embeddings):
    """Categorize a list of questions, ensuring valid output format."""
    categorized_questions = []

    if not isinstance(questions, list):
        print(f"⚠ Invalid question format received (not a list): {questions}")
        return []

    for question in questions:
        if not isinstance(question, str) or len(question) < 5:  # ✅ Ignore short/invalid inputs
            print(f"⚠ Skipping invalid question format: {question}")
            continue
        
        question_embedding = model.encode(question, convert_to_tensor=True)

        # Compare the question with all category embeddings using cosine similarity
        similarities = {
            category: util.pytorch_cos_sim(question_embedding, embeddings).mean().item()
            for category, embeddings in category_embeddings.items()
        }

        if not similarities:  # ✅ Handle empty case
            print(f"⚠ Warning: No similarities found for '{question}'")
            continue

        best_category = max(similarities, key=similarities.get)

        print(f"🔍 Debug: Categorized '{question}' as '{best_category}'")

        # ✅ Append full question instead of a nested list
        categorized_questions.append({"question": question, "category": best_category})

    return categorized_questions  # ✅ Ensures a flat list of dictionaries
    # return questions


def filter_questions(mind_data, new_questions):
    """Filters out duplicate, near-duplicate, or answered questions before storing."""
    print(f"🔍 Debug: filter_questions() received {len(new_questions)} questions")

    if not new_questions:
        print("⚠ No new questions received, stopping filtering early!")
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
            print(f"⚠ Unexpected question format (not dict with 'question' key): {question_entry}")
            continue  # Skip invalid entries

        if not question_text or len(question_text) < 6:
            print(f"⚠ Ignoring invalid question (too short or empty): {question_text}")
            continue

        question_text_lower = question_text.lower()

        # ✅ Reject dictionary definitions explicitly before filtering
        if question_text_lower in stored_knowledge_set and not question_text_lower.startswith("📖"):
            print(f"⚠ WARNING: Possible false positive → Skipping '{question_text}' (already in stored knowledge)")
            continue  # 🚨 Prevents accidentally removing legitimate questions!

        is_duplicate = any(fuzz.ratio(question_text_lower, existing_text) > 65 for existing_text in existing_questions)

        if not is_duplicate:
            filtered_questions.append(question_entry)
            print(f"✅ Accepted New Question: {question_text}")

    print(f"🔍 Debug: {len(filtered_questions)} questions passed filtering and will be added.")

    return filtered_questions
