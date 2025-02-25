import random
import time
import sys
import os
import fuzzywuzzy
try:
    from fuzzywuzzy import fuzz
    fuzzy_available = True
except ImportError:
    print("⚠ FuzzyWuzzy module not found, falling back to exact matching.")
    fuzzy_available = False

# Add the parent directory (astra_reflections) to sys.path so Python can find `astra_core`
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from astra_core.config_loader import load_config
from sentence_transformers import SentenceTransformer, util

# Load question config
question_config = load_config("question_config")  # Use the absolute path to the config file

# Debugging: Check the loaded config structure
print(f"Loaded Config: {question_config}")

# Ensure 'question_categories' exists in the loaded config
if 'question_categories' not in question_config:
    raise KeyError("'question_categories' not found in the config!")

# Initialize the Sentence-BERT model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def generate_category_embeddings(question_config):
    """Generate embeddings for each category's sample questions."""
    category_embeddings = {}

    # Debugging: Print the entire question_config to inspect its structure
    print(f"Loaded question_config: {question_config}")

    # Check if 'question_categories' exists in the config
    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    # Debugging: Print the keys within 'question_categories' to ensure it's what we expect
    print(f"Keys in 'question_categories': {list(question_config['question_categories'].keys())}")

    # Generate embeddings for each category's sample questions
    for category, details in question_config["question_categories"].items():
        # Debugging: Print out the category and its details
        print(f"Processing category: {category}")
        print(f"Category Details: {details}")
        
        sample_questions = details.get("sample_questions", [])
        
        # Debugging: Print out the sample questions for this category
        print(f"Sample Questions for category '{category}': {sample_questions}")
        
        # Ensure there are sample questions before encoding them
        if not sample_questions:
            print(f"⚠ Warning: No sample questions found for category '{category}'")
        else:
            # Generate embeddings for the sample questions
            category_embeddings[category] = model.encode(sample_questions, convert_to_tensor=True)

    # Debugging: Print the generated embeddings
    print(f"Generated category embeddings: {category_embeddings}")

    return category_embeddings

# Generate embeddings for all categories
category_embeddings = generate_category_embeddings(question_config)

def categorize_question(question, category_embeddings):
    """Categorize an incoming question based on semantic similarity to category embeddings."""
    # Encode the incoming question
    question_embedding = model.encode(question, convert_to_tensor=True)

    # Debugging: Print the question and its embedding
    print(f"Categorizing Question: {question}")
    print(f"Question Embedding: {question_embedding}")

    # Compare the question with all category embeddings using cosine similarity
    similarities = {}
    for category, embeddings in category_embeddings.items():
        similarities[category] = util.pytorch_cos_sim(question_embedding, embeddings).mean().item()

    # Debugging: Print similarities for each category
    print(f"Similarities: {similarities}")
    
    # Return the category with the highest similarity
    best_category = max(similarities, key=similarities.get)
    print(f"Best Category: {best_category}")
    return best_category

def filter_questions(mind_data, new_questions):
    """Filters out duplicate, near-duplicate, or answered questions before storing."""
    filtered_questions = []
    stored_knowledge = [k.lower() for k in mind_data.get("stored_knowledge", [])]
    
    # ✅ Store existing questions with their metadata for smarter deduplication
    existing_questions = [
        (q["question"].lower(), q.get("source", "").lower(), q.get("context_summary", "").lower(), q.get("related_knowledge", "").lower()) 
        for q in mind_data.get("self_questions", []) if isinstance(q, dict)
    ]
    
    # Debugging: Print the existing questions
    print(f"Existing Questions: {existing_questions}")

    for question_entry in new_questions:
        if isinstance(question_entry, dict) and "question" in question_entry:
            question_text = question_entry["question"].strip().lower()
            question_source = question_entry.get("source", "").strip().lower()
            question_context = question_entry.get("context_summary", "").strip().lower()
            question_related = question_entry.get("related_knowledge", "").strip().lower()
        else:
            print(f"⚠ Unexpected question format: {question_entry}")
            continue  # Skip invalid entries

        # Debugging: Print the current question being processed
        print(f"Processing Question: {question_text}")

        # ✅ Check if an answer already exists in stored knowledge
        if any(question_text in knowledge.lower() for knowledge in stored_knowledge):
            print(f"✅ Answer found! Archiving question: {question_text}")
            continue

        # ✅ Context-aware deduplication: Compare full question with source, context, and related knowledge
        is_duplicate = False
        for existing_text, existing_source, existing_context, existing_related in existing_questions:
            similarity_score = fuzz.ratio(question_text, existing_text) if fuzzy_available else 0

            # Debugging: Print similarity scores
            print(f"Similarity score for '{question_text}' and '{existing_text}': {similarity_score}")
            
            # ✅ If text is highly similar (85%+) and source/context/related knowledge all match → skip as duplicate
            if (
                similarity_score > 85
                and existing_source == question_source
                and existing_context == question_context
                and existing_related == question_related
            ):
                print(f"⚠ Near-duplicate question skipped (with context): {question_text}")
                is_duplicate = True
                break

        if not is_duplicate:
            filtered_questions.append(question_entry)
            print(f"🧐 New Question Added: {question_text}")

    return filtered_questions

# Sample question for testing
question = "What is the meaning of life?"

# Categorize the question
category = categorize_question(question, category_embeddings)

# Output the result
print(f"Question: {question}")
print(f"Category: {category}")
