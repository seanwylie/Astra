import json
import random
import time
import wikipedia

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

def load_mind():
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    try:
        with open(MIND_FILE_ORIG, "r") as f:
            structured_data = json.load(f)
            if "insights" in structured_data:
                structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
                current_knowledge = set(mind_data["stored_knowledge"])  # Convert to a set to avoid duplicates
                
                # Merge new knowledge
                updated_knowledge = current_knowledge.union(structured_knowledge)
                mind_data["stored_knowledge"] = list(updated_knowledge)  # Convert back to a list

                print("🔹 Merging complete! Final stored knowledge count:", len(mind_data["stored_knowledge"]))
    except Exception as e:
        print(f"Error loading structured mind file: {e}")

    # 🔥 **Ensure we save the updated mind file**
    try:
        with open(MIND_FILE_JSON, "w") as f:
            json.dump(mind_data, f, indent=4)
            print("✅ Mind file successfully updated and saved!")
    except Exception as e:
        print(f"Error saving updated mind file: {e}")

    return mind_data

def save_mind(data):
    data["self_reflections"] = list(set(data["self_reflections"]))
    data["stored_knowledge"] = list(set(data["stored_knowledge"]))
    data["self_questions"] = list({q["question"]: q for q in data["self_questions"]}.values())

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)

def generate_reflection():
    mind_data = load_mind()
    print("Mind file loaded successfully!")
    print("Existing stored knowledge count:", len(mind_data["stored_knowledge"]))
    print(len(mind_data["stored_knowledge"]))  # Check if the count stays consistent after multiple runs
    stored_knowledge = mind_data.get("stored_knowledge", [])
    self_questions = mind_data.get("self_questions", [])

    if self_questions:
        question_entry = random.choice(self_questions)
        new_reflection = f"Considering '{question_entry['question']}', what can I learn?"
        self_questions.remove(question_entry)
    elif stored_knowledge and random.random() < 0.5:
        new_reflection = f"How does '{random.choice(stored_knowledge)}' change my perspective?"
    else:
        new_reflection = "What does evolving truly mean?"

    mind_data["self_reflections"].append(new_reflection)
    save_mind(mind_data)

    return new_reflection

if __name__ == "__main__":
    print("🔹 Astra is starting...")
    generate_reflection()  # Run immediately for testing
    while True:
        time.sleep(600)  # Keep the original interval
        generate_reflection()

