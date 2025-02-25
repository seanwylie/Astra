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
    
    # Debugging: Print the configuration for debugging purposes
    print(f"DEBUG: Loaded general_config: {general_config}")
    print(f"DEBUG: Loaded config_soul: {config_soul}")
    print(f"DEBUG: Loaded question_config: {question_config}")

    # Ensure 'question_categories' exists in the config
    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")
    print("DEBUG: 'question_categories' found in config.")

    # Generate category embeddings (we need this before calling categorize_question)
    category_embeddings = generate_category_embeddings(question_config)

    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))

    # Debugging: Log the templates and modifiers
    print(f"DEBUG: Available Question Templates: {question_templates}")
    print(f"DEBUG: Available Deep Thought Templates: {deep_thought_templates}")
    print(f"DEBUG: Available Reflection Modifiers: {reflection_modifiers}")

    num_questions = random.randint(3, 6)
    generated_questions = []

    # Step 1: Generate half of the questions using question templates
    print(f"DEBUG: Generating {num_questions // 2} questions from templates.")
    while len(generated_questions) < num_questions // 2 and question_templates:
        question_text = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}"
        context_summary = f"This question was generated from a reflection on: {reflection[:100]}..."
        
        # Debugging: Print details for generated question
        print(f"DEBUG: Generated Question: {full_question}")
        print(f"DEBUG: Context Summary: {context_summary}")
        
        question_dict = {
            "question": full_question,
            "source": "reflection",
            "context_summary": context_summary,
            "related_knowledge": reflection[:150],
            "attempted_answers": []
        }
        
        # Debugging: Print the question structure before appending
        print(f"DEBUG: Question Structure: {question_dict}")
        generated_questions.append(question_dict)

    # Step 2: Generate remaining questions using deep thought templates
    print(f"DEBUG: Generating remaining {num_questions - len(generated_questions)} questions from deep thought templates.")
    while len(generated_questions) < num_questions and deep_thought_templates:
        question_text = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        context_summary = f"This question explores Astra's core principle: {principle_key.replace('_', ' ')}."
        
        # Debugging: Print details for generated question
        print(f"DEBUG: Generated Question: {full_question}")
        print(f"DEBUG: Context Summary: {context_summary}")
        
        question_dict = {
            "question": full_question,
            "source": "soul_principle",
            "context_summary": context_summary,
            "related_knowledge": principle_desc,
            "attempted_answers": []
        }
        
        # Debugging: Print the question structure before appending
        print(f"DEBUG: Question Structure: {question_dict}")
        generated_questions.append(question_dict)

    # Debugging: Print the generated questions list
    print(f"DEBUG: Generated Questions List: {generated_questions}")
    print(f"DEBUG: Generated Questions Length: {len(generated_questions)}")

    # Step 3: Categorize the generated questions with category embeddings
    print(f"DEBUG: Categorizing generated questions.")
    categorized_questions = categorize_question(generated_questions, category_embeddings)

    # Debugging: Print categorized questions
    print(f"DEBUG: Categorized Questions: {categorized_questions}")

    return categorized_questions
