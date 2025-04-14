from astra_core.config_loader import load_config, debug_log
import random
from astra_core.questions.question_utils import generate_category_embeddings, categorize_question
from astra_core.knowledge_manager import load_mind

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")
question_config = load_config("question_config")

def generate_questions(reflection: str, mind_data: dict) -> tuple:
    """Generates structured questions based on Astra's reflection while ensuring variety & avoiding redundancy."""
    
    debug_log("Loading")
    fresh_mind_data = load_mind()
    stored_knowledge = fresh_mind_data.get("stored_knowledge", [])
    unresolved_questions = fresh_mind_data.get("unresolved_questions", [])

    print(f"🔍 Loaded fresh mind data. Stored Knowledge: {len(stored_knowledge)}, Unresolved Questions: {len(unresolved_questions)}")

    unresolved_limit = 1000
    if len(unresolved_questions) >= unresolved_limit:
        print(f"⚠ WARNING: Too many unresolved questions ({len(unresolved_questions)}). Skipping new question generation.")
        return {}, {}

    question_categories = question_config.get("question_categories", ["general", "scientific", "philosophical"])
    category_embeddings = generate_category_embeddings(question_config)

    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))

    num_questions = random.randint(3, 6)
    generated_questions = set()
    category_counts = {category: 0 for category in question_categories}

    # Step 1: Generate Questions from Templates
    while len(generated_questions) < num_questions // 3 and question_templates:
        question_text = random.choice(question_templates).strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}".strip()
        generated_questions.add(full_question)

    # Step 2: Generate Deep Thought Questions
    while len(generated_questions) < num_questions // 2 and deep_thought_templates:
        question_text = random.choice(deep_thought_templates).strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        generated_questions.add(full_question)

    # Step 3: Generate Questions from Stored Knowledge
    knowledge_sample = random.sample(stored_knowledge, min(5, len(stored_knowledge)))
    for knowledge_entry in knowledge_sample:
        if len(generated_questions) >= num_questions:
            break
        if len(knowledge_entry) > 10:
            knowledge_question = f"How does this knowledge refine my understanding? {knowledge_entry[:150]}..."
            generated_questions.add(knowledge_question)

    # Step 4: Revisit Unresolved Questions
    unresolved_sample = random.sample(unresolved_questions, min(3, len(unresolved_questions)))
    for unresolved in unresolved_sample:
        if len(generated_questions) >= num_questions:
            break
        unresolved_question = unresolved["question"]
        unresolved_followup = f"What new insights could help resolve this? {unresolved_question}"
        generated_questions.add(unresolved_followup)

    print(f"🔍 Debug: Generated unique questions: {list(generated_questions)}")

    # Step 5: Categorize Questions
    categorized_questions = []
    for question in generated_questions:
        if isinstance(question, str) and len(question) > 6:
            category = categorize_question([question], category_embeddings)
            if category:
                categorized_questions.append({"question": question.strip(), "category": category[0]["category"]})
                category_counts[category[0]["category"]] += 1
            else:
                print(f"⚠ Warning: No category found for question: {question}")

    print(f"🔍 Debug: Categorized questions: {categorized_questions}")
    print(f"🔍 Debug: Question category counts: {category_counts}")

    # Step 6: Store & Format
    if categorized_questions:
        mind_data["self_questions"].extend([q["question"] for q in categorized_questions])

    # Step 7: Limit Question Overload
    if len(mind_data["self_questions"]) > unresolved_limit:
        print(f"⚠ WARNING: Too many unresolved questions ({len(mind_data['self_questions'])}). Trimming to {unresolved_limit}.")
        mind_data["self_questions"] = mind_data["self_questions"][-unresolved_limit:]

    return {"general": mind_data["self_questions"]}, category_counts