import random
import time
from astra_interfaces.influence import load_mind, save_mind
from astra_core.knowledge import knowledge_manager
from astra_core.config_loader import load_config

general_config = load_config("general_config")
config_soul = load_config("config_soul")  # Load deeper soul-based questioning parameters

def generate_questions(reflection, mind_data):
    """Generates structured questions based on Astra's reflection, ensuring variety and avoiding redundancy."""
    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))

    num_questions = random.randint(3, 6)
    generated_questions = []

    while len(generated_questions) < num_questions // 2 and question_templates:
        question_text = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}"
        context_summary = f"This question was generated from a reflection on: {reflection[:100]}..."

        generated_questions.append({
            "question": full_question,
            "source": "reflection",
            "context_summary": context_summary,
            "related_knowledge": reflection[:150],
            "attempted_answers": []
        })

    while len(generated_questions) < num_questions and deep_thought_templates:
        question_text = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        context_summary = f"This question explores Astra's core principle: {principle_key.replace('_', ' ')}."

        generated_questions.append({
            "question": full_question,
            "source": "soul_principle",
            "context_summary": context_summary,
            "related_knowledge": principle_desc,
            "attempted_answers": []
        })

    print("✅ Debug: Generated full-length questions with context:")
    for q in generated_questions:
        print(f"- {q['question']} (Source: {q['source']}, Context: {q['context_summary']}, Related Knowledge: {q['related_knowledge'][:50]}...)")

    return categorize_questions(filter_questions(mind_data, generated_questions))

def filter_questions(mind_data, new_questions):
    """Filters out duplicate or answered questions before storing."""
    filtered_questions = []
    stored_knowledge = [k.lower() for k in mind_data.get("stored_knowledge", [])]
    existing_questions = [q["question"].lower() for q in mind_data.get("self_questions", []) if isinstance(q, dict)]

    for question_entry in new_questions:
        if isinstance(question_entry, dict) and "question" in question_entry:
            question_text = question_entry["question"].strip().lower()
        else:
            print(f"⚠ Unexpected question format: {question_entry}")
            continue  # Skip invalid entries

        # ✅ Prevent exact or highly similar duplicates
        if any(question_text == knowledge.lower() for knowledge in stored_knowledge):
            print(f"✅ Answer found! Archiving question: {question_text}")
            continue

        if any(question_text in q or q in question_text for q in existing_questions):
            print(f"⚠ Duplicate question skipped: {question_text}")
            continue

        filtered_questions.append(question_entry)
        print(f"🧐 New Question Added: {question_text}")

    return filtered_questions

def categorize_question_type(question_text):
    """Categorizes a question into a single theme based on keywords."""
    categories = {
        "philosophical": ["ethics", "values", "morality", "meaning"],
        "introspective": ["identity", "self", "perspective"],
        "knowledge": ["facts", "science", "history", "how"],
    }

    for category, keywords in categories.items():
        if any(keyword in question_text.lower() for keyword in keywords):
            return category
    return "general"  # ✅ Default category

def categorize_questions(questions):
    """Categorizes questions into themes such as philosophical, introspective, knowledge-based, etc."""
    categorized_questions = {"general": []}
    category_counts = {"general": 0, "introspective": 0, "knowledge": 0}

    for question_entry in questions:
        if isinstance(question_entry, dict) and "question" in question_entry:
            category = categorize_question_type(question_entry["question"])
        else:
            print(f"⚠ Unexpected question format in categorize_questions: {question_entry}")
            continue  # Skip invalid entries

        categorized_questions.setdefault(category, []).append(question_entry)
        category_counts[category] += 1

    return categorized_questions, category_counts

def process_new_questions(reflection):
    """Pipeline to generate, filter, categorize, and analyze Astra's thought patterns."""
    mind_data = load_mind()
    categorized_questions, category_counts = generate_questions(reflection, mind_data)

    new_questions = []
    for category, questions in categorized_questions.items():
        for question_entry in questions:
            if isinstance(question_entry, dict) and "question" in question_entry:
                new_questions.append(question_entry)

    if new_questions:
        print(f"✅ Debug: Adding {len(new_questions)} new questions to self_questions")
        mind_data["self_questions"].extend(new_questions)

    mind_data["self_question_categories"] = category_counts  # ✅ Store category counts for dinner-time discussion

    save_mind(mind_data)

def track_question_patterns(mind_data):
    """Analyzes the last 100 self-questions, categorizes recurring themes, and adjusts future question weighting."""
    recent_questions = mind_data.get("self_questions", [])[-100:]
    question_patterns = {}

    for question_entry in recent_questions:
        # ✅ Ensure we're processing a dictionary with a "question" key
        if isinstance(question_entry, dict) and "question" in question_entry:
            category = categorize_question_type(question_entry["question"])
        else:
            print(f"⚠ Unexpected question format in track_question_patterns: {question_entry}")
            continue  # Skip invalid entries

        question_patterns[category] = question_patterns.get(category, 0) + 1

    mind_data["self_question_patterns"] = question_patterns  # ✅ Store tracking data in mind file
    print(f"✅ Debug: Updated question patterns: {question_patterns}")
