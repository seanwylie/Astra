import json

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_ORIG = "mind_file_sean.json"

def load_mind():
    """Load Astra's mind file while ensuring structured knowledge is merged and memory is managed properly."""
    print("🔍 Debug: Loading mind files...")

    mind_data = {
        "self_reflections": [],
        "self_questions": [],
        "stored_knowledge": [],
    }

    try:
        # ✅ Load mind_file.json (self-reflections + questions)
        with open(MIND_FILE_JSON, "r", encoding="utf-8") as f:
            mind_data = json.load(f)
            print(f"✅ Loaded {len(mind_data['self_reflections'])} reflections, {len(mind_data['self_questions'])} questions.")

    except FileNotFoundError:
        print("⚠ Warning: mind_file.json not found. Starting with an empty mind.")

    # ✅ Merge structured knowledge from mind_file_sean.json
    try:
        with open(MIND_FILE_ORIG, "r", encoding="utf-8") as f:
            structured_data = json.load(f)

            if "insights" in structured_data:
                structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
                current_knowledge = set(mind_data["stored_knowledge"])

                # ✅ Merge knowledge but don't overwrite reflections
                updated_knowledge = current_knowledge.union(structured_knowledge)
                mind_data["stored_knowledge"] = list(updated_knowledge)

                print(f"🔹 Merging complete! Final stored knowledge count: {len(mind_data['stored_knowledge'])}")

    except Exception as e:
        print(f"⚠ Error loading structured mind file: {e}")

    return mind_data



def save_mind(mind_data):
    """Saves updated knowledge to Astra’s mind file while ensuring no nested structures exist."""
    print("🔍 Debug: Sanitizing mind file before saving...")

    # ✅ Ensure all fields are flat lists of strings
    mind_data["self_reflections"] = [str(item) for item in mind_data.get("self_reflections", []) if isinstance(item, str)]
    mind_data["self_questions"] = [str(item) for item in mind_data.get("self_questions", []) if isinstance(item, str)]
    mind_data["stored_knowledge"] = [str(item) for item in mind_data.get("stored_knowledge", []) if isinstance(item, str)]

    # ✅ Save back to mind_file.json
    with open(MIND_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(mind_data, f, indent=4)

    print(f"✅ Mind file saved successfully! Reflections: {len(mind_data['self_reflections'])}, Questions: {len(mind_data['self_questions'])}, Knowledge: {len(mind_data['stored_knowledge'])}")


def store_knowledge(new_knowledge):
    """Adds new knowledge to Astra’s memory."""
    mind_data = load_mind()
    mind_data["stored_knowledge"].append(new_knowledge)
    save_mind(mind_data)
