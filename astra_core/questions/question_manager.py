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
    mood_score = mind_data.get("mood_score", 0)
    
    num_questions = random.randint(3, 6)  # Increase range for depth
    
    generated_questions = set()
    while len(generated_questions) < num_questions // 2 and question_templates:
        question = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        generated_questions.add(f"{question} {modifier}")
    
    while len(generated_questions) < num_questions and deep_thought_templates:
        question = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        generated_questions.add(f"{question} How does this relate to {principle_desc}?")
    
    print("✅ Debug: Generated full-length questions:")
    for q in generated_questions:
        print(f"- {q} (Length: {len(q)})")
    
    return track_question_lifecycle(categorize_questions(filter_questions(mind_data, list(generated_questions))))

def filter_questions(mind_data, new_questions):
    """Filters out duplicate or answered questions before storing."""
    filtered_questions = []
    stored_knowledge = [k.lower() for k in mind_data.get("stored_knowledge", [])]
    existing_questions = [q.lower() for q in mind_data.get("self_questions", [])]
    
    for question in new_questions:
        question_core = question.strip().lower()
        
        if any(question_core in k for k in stored_knowledge):
            print(f"✅ Answer found! Skipping: {question}")
            continue
        
        if any(question_core in q for q in existing_questions):
            print(f"⚠ Duplicate detected: {question}")
            continue
        
        filtered_questions.append(question)
    
    return filtered_questions

def track_question_lifecycle(questions):
    """Adds a timestamp to track when questions are created."""
    timestamp = time.time()
    return {category: [{"question": q, "created_at": timestamp} for q in qs] for category, qs in questions.items()}

def categorize_questions(questions):
    """Categorizes questions into themes such as philosophical, introspective, knowledge-based, etc."""
    categories = {
        "philosophical": ["ethics", "values", "morality", "meaning"],
        "introspective": ["identity", "self", "perspective"],
        "knowledge": ["facts", "science", "history", "how"],
    }
    categorized_questions = {"general": []}
    
    for question in questions:
        category = "general"
        for cat, keywords in categories.items():
            if any(keyword in question.lower() for keyword in keywords):
                category = cat
                break
        categorized_questions.setdefault(category, []).append(question)
    
    return categorized_questions

def track_question_patterns(mind_data):
    """Analyzes the last 100 self-questions, categorizes recurring themes, and adjusts future question weighting."""
    recent_questions = mind_data.get("self_questions", [])[-100:]
    question_patterns = {}
    
    for question in recent_questions:
        category = categorize_question_type(question)
        question_patterns[category] = question_patterns.get(category, 0) + 1
    
    return question_patterns

def categorize_question_type(question):
    """Categorizes a question based on keywords."""
    categories = {
        "philosophical": ["ethics", "values", "morality", "meaning"],
        "introspective": ["identity", "self", "perspective"],
        "knowledge": ["facts", "science", "history", "how"],
    }
    
    for category, keywords in categories.items():
        if any(keyword in question.lower() for keyword in keywords):
            return category
    return "general"

def process_new_questions(reflection):
    """Pipeline to generate, filter, categorize, and analyze Astra's thought patterns."""
    mind_data = load_mind()
    new_questions = generate_questions(reflection, mind_data)

    if new_questions:
        print(f"✅ Debug: Adding {len(new_questions)} new questions to self_questions")
        mind_data["self_questions"].extend(new_questions)  # ✅ Store new questions before saving

    track_question_patterns(mind_data)
    save_mind(mind_data)

