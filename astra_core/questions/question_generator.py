import sys
import os
import random
from astra_core.config_loader import load_config
from astra_core.questions.question_utils import generate_category_embeddings, categorize_question
from astra_core.questions.question_flagger import flag_unresolved_question

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")
question_config = load_config("question_config")

def generate_questions(reflection, mind_data):
    """Generates structured questions based on Astra's reflection and existing knowledge, ensuring variety and avoiding redundancy."""

    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    category_embeddings = generate_category_embeddings(question_config)

    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))
    stored_knowledge = mind_data.get("stored_knowledge", [])
    unresolved_questions = mind_data.get("unresolved_questions", [])

    num_questions = random.randint(3, 6)
    generated_questions = []

    ### ✅ **Step 1: Generate Questions from Templates**
    while len(generated_questions) < num_questions // 2 and question_templates:
        question_text = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}"
        generated_questions.append(full_question)

    ### ✅ **Step 2: Generate Deep Thought Questions**
    while len(generated_questions) < num_questions and deep_thought_templates:
        question_text = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        generated_questions.append(full_question)

    ### ✅ **Step 3: Generate Questions from Stored Knowledge**
    for knowledge_entry in stored_knowledge:
        if len(generated_questions) >= num_questions:
            break  

        if len(knowledge_entry) > 10:
            knowledge_question = f"How does this knowledge refine my understanding? {knowledge_entry[:100]}..."
            generated_questions.append(knowledge_question)

    ### ✅ **Step 4: Revisit Unresolved Questions**
    for unresolved in unresolved_questions:
        if len(generated_questions) >= num_questions:
            break  

        unresolved_question = unresolved["question"]
        unresolved_followup = f"What new insights could help resolve this? {unresolved_question}"
        generated_questions.append(unresolved_followup)

    print(f"🔍 Debug: Generated questions: {generated_questions}")
    print(f"🔍 Debug: Reflection input: {reflection}")
    print(f"🔍 Debug: Stored knowledge count: {len(mind_data['stored_knowledge'])}")

    ### ✅ **Step 5: Categorize Questions and Ensure Proper Formatting**
    categorized_questions = []
    for question in generated_questions:
        if isinstance(question, str) and len(question) > 6:
            category = categorize_question(question, category_embeddings)
            if category:
                categorized_questions.append({"question": question.strip(), "category": category})

    print(f"🔍 Debug: Categorized questions: {categorized_questions}")

    ### ✅ **Step 6: Flag Unresolved Questions**
    flagged_questions = flag_unresolved_question([q["question"] for q in categorized_questions], mind_data) or []
    print(f"🔍 Debug: Flagged unresolved questions: {flagged_questions}")

    ### ✅ **Step 7: Cleanup Question Formatting**
    flagged_questions = [
        str(q).strip() for q in flagged_questions if isinstance(q, str) and len(q) > 6
    ]

    final_questions = [q.split("?", 1)[0].strip() + "?" for q in flagged_questions if q]

    categorized_questions = {"general": final_questions} if isinstance(final_questions, list) else final_questions
    return categorized_questions, {}
