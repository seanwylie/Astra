import sys
import os
import random
from astra_core.config_loader import load_config
from astra_core.questions.question_utils import generate_category_embeddings, categorize_question
from astra_core.questions.question_flagger import flag_unresolved_question
from astra_core.knowledge_manager import load_mind  # Ensure this import is correct
from astra_core.config_loader import debug_log

# Load configuration files
general_config = load_config("general_config")
config_soul = load_config("config_soul")
question_config = load_config("question_config")

def generate_questions(reflection, mind_data):
    """Generates structured questions based on Astra's reflection and existing knowledge, ensuring variety and avoiding redundancy."""

    # 🔥 Explicitly load the latest mind data before manipulating it
    debug_log("Loading")  
    fresh_mind_data = load_mind()  # Ensure the latest knowledge state is retrieved
    stored_knowledge = fresh_mind_data.get("stored_knowledge", [])
    unresolved_questions = fresh_mind_data.get("unresolved_questions", [])

    print(f"🔍 Loaded fresh mind data. Stored Knowledge: {len(stored_knowledge)}, Unresolved Questions: {len(unresolved_questions)}")

    if 'question_categories' not in question_config:
        raise KeyError("'question_categories' not found in the config!")

    category_embeddings = generate_category_embeddings(question_config)

    question_templates = list(set(general_config.get("question_templates", [])))
    deep_thought_templates = list(set(config_soul.get("deep_thought_questions", [])))
    principles = config_soul.get("soul", {}).get("principles", {})
    reflection_modifiers = list(set(general_config.get("reflection_style_modifiers", {}).values()))

    num_questions = random.randint(3, 6)
    generated_questions = set()  # ✅ Use a set to prevent duplicates
    category_counts = {category: 0 for category in question_config["question_categories"]}  # ✅ Initialize category tracking

    ### ✅ **Step 1: Generate Questions from Templates**
    while len(generated_questions) < num_questions // 2 and question_templates:
        question_text = f"{random.choice(question_templates)}".strip()
        modifier = random.choice(reflection_modifiers)
        full_question = f"{question_text} {modifier}".strip()
        generated_questions.add(full_question)

    ### ✅ **Step 2: Generate Deep Thought Questions**
    while len(generated_questions) < num_questions and deep_thought_templates:
        question_text = f"{random.choice(deep_thought_templates)}".strip()
        principle_key = random.choice(list(principles.keys()))
        principle_desc = principles[principle_key]["description"]
        full_question = f"{question_text} How does this relate to my principle of {principle_key.replace('_', ' ')}: {principle_desc}?"
        generated_questions.add(full_question)

    ### ✅ **Step 3: Generate Questions from Stored Knowledge**
    for knowledge_entry in stored_knowledge:
        if len(generated_questions) >= num_questions:
            break  

        if len(knowledge_entry) > 10:
            knowledge_question = f"How does this knowledge refine my understanding? {knowledge_entry[:100]}..."
            generated_questions.add(knowledge_question)

    ### ✅ **Step 4: Revisit Unresolved Questions**
    for unresolved in unresolved_questions:
        if len(generated_questions) >= num_questions:
            break  

        unresolved_question = unresolved["question"]
        unresolved_followup = f"What new insights could help resolve this? {unresolved_question}"
        generated_questions.add(unresolved_followup)

    print(f"🔍 Debug: Generated unique questions: {list(generated_questions)}")
    print(f"🔍 Debug: Reflection input: {reflection}")
    print(f"🔍 Debug: Stored knowledge count after reloading: {len(stored_knowledge)}")

    ### ✅ **Step 5: Categorize Questions & Ensure Proper Formatting**
    categorized_questions = []
    for question in generated_questions:
        if isinstance(question, str) and len(question) > 6:
            print(f"🔍 Debug: Attempting to categorize question: {question}")  # Debugging

            # ✅ FIX: Ensure we pass a single string, not a list
            category = categorize_question([question], category_embeddings)


            if not category:
                print(f"⚠ Warning: No category found for question: {question}")
            else:
                print(f"✅ Categorized '{question}' as: {category}")

            if category:
                categorized_questions.append({"question": question.strip(), "category": category[0]["category"]})
                category_counts[category[0]["category"]] += 1  # ✅ Track first assigned category

    print(f"🔍 Debug: Categorized questions: {categorized_questions}")
    print(f"🔍 Debug: Question category counts: {category_counts}")

    ### ✅ **Step 6: Store Categorized Questions Before Filtering**
    if categorized_questions:
        categorized_question_list = [q["question"] for q in categorized_questions]  # ✅ Extract only questions
        print(f"✅ Debug: Adding categorized questions to mind_data: {categorized_question_list}")
        mind_data["self_questions"].extend(categorized_question_list)
    else:
        print(f"⚠ Warning: No categorized questions were added to mind_data!")

    ### ✅ **Step 7: Flag Unresolved Questions**
    flagged_questions = flag_unresolved_question(categorized_question_list, fresh_mind_data) or []
    print(f"🔍 Debug: Flagged unresolved questions: {flagged_questions}")

    ### ✅ **Step 8: Cleanup & Format Final Questions**
    final_questions = []
    for q in flagged_questions:
        if isinstance(q, str) and len(q) > 6:
            formatted_q = q.strip()
            if not formatted_q.endswith("?"):  # ✅ Ensure all questions end with "?"
                formatted_q += "?"
            final_questions.append(formatted_q)

    ### ✅ **Fix: Ensure returned questions are in correct format**
    return {"general": final_questions}, category_counts  # ✅ Return two values now!
