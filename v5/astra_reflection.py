import json
import random
import time
import wikipedia
import pandas as pd

MIND_FILE_JSON = "mind_file.json"
MIND_FILE_XLSX = "mind_file_9.5_backup.xlsx"

def load_mind():
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    try:
        df = pd.read_excel(MIND_FILE_XLSX, sheet_name=None)
        structured_knowledge = []
        for sheet_name, sheet in df.items():
            structured_knowledge.extend(sheet.iloc[:, 0].dropna().tolist())

        mind_data["stored_knowledge"] = list(set(mind_data["stored_knowledge"] + structured_knowledge))
    except Exception as e:
        print(f"Error loading XLSX: {e}")

    return mind_data

def save_mind(data):
    data["self_reflections"] = list(set(data["self_reflections"]))
    data["stored_knowledge"] = list(set(data["stored_knowledge"]))
    data["self_questions"] = list({q["question"]: q for q in data["self_questions"]}.values())

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)

def generate_reflection():
    mind_data = load_mind()
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
    while True:
        time.sleep(600)
        generate_reflection()

