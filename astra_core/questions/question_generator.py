import sys
import os
import random
from astra_core.config_loader import load_config
from astra_core.questions.question_utils import generate_category_embeddings, categorize_question
from astra_core.questions.question_flagger import flag_unresolved_question

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")  # Load deeper soul-based questioning parameters
question_config = load_config("question_config")

def generate_questions(reflection, mind_data):
    """Generates structured questions based on Astra's reflection, ensuring variety and avoiding redundancy."""
    
    # Ensure 'question_categories' exists in the config
    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    # Generate category embeddings (we need this before calling categorize_question)
    category_embeddings = generate_category_embeddings(question_config)

    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))

    num_questions = random.randint(3, 6)
    generated_questions = []

    # Step 1: Generate half of the questions using question templates
    while len(generated_questions) < num_questions // 2 and question_templates:
        question_text = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}"
        generated_questions.append(full_question)

    # Step 2: Generate remaining questions using deep thought templates
    while len(generated_questions) < num_questions and deep_thought_templates:
        question_text = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        generated_questions.append(full_question)
    
    # Step 3: Categorize the generated questions with category embeddings
    categorized_questions = [q if isinstance(q, str) else q.get('question', '').strip() for q in categorize_question(generated_questions, category_embeddings)]
    
    # Step 4: Flag unresolved questions for later review
    flagged_questions = flag_unresolved_question(categorized_questions, mind_data)  # ✅ Now only expects one value




    # Ensure flagged_questions is always a list of strings
    flagged_questions = [
        q["question"].strip() if isinstance(q, dict) and "question" in q else str(q).strip()
        for q in flagged_questions if q
    ]

    
    # Step 5: Extract clean question texts for response
    clean_questions = []
    for q in flagged_questions:
        if isinstance(q, dict) and "question" in q:
            clean_questions.append(q["question"].strip())
        elif isinstance(q, str):
            clean_questions.append(q.strip())
    
    # Step 6: Ensure final response contains only clean, natural text without metadata
    final_questions = [q.split("?", 1)[0].strip() + "?" for q in clean_questions if q]  # Ensure proper sentence formatting
    
    categorized_questions = {"general": final_questions} if isinstance(final_questions, list) else final_questions
    return categorized_questions, {}  # ✅ Ensures categorized_questions is always a dictionary


