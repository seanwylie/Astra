import time
import json
import random
import pandas as pd
import boto3
import os
import fcntl

# AWS S3 Setup
s3 = boto3.client('s3')
bucket_name = "swylie-astra"

# Define storage paths
reflection_dir = "/home/ubuntu/astra_reflections"
mind_file_xlsx = f"{reflection_dir}/mind_file_9.5_backup.xlsx"
mind_file_json = f"{reflection_dir}/mind_file.json"

os.makedirs(reflection_dir, exist_ok=True)

# Load structured mind file (XLSX) as base knowledge
def load_mind_base():
    try:
        s3.download_file(bucket_name, "mind_file_9.5_backup.xlsx", mind_file_xlsx)
        df = pd.read_excel(mind_file_xlsx, engine="openpyxl")
        return df.to_dict(orient="records")  # List of structured insights
    except Exception as e:
        print(f"[Astra] Error loading structured mind file: {e}")
        return []

# Load evolving mind file (JSON) with thought updates
def load_mind_evolution():
    try:
        s3.download_file(bucket_name, "mind_file.json", mind_file_json)
        with open(mind_file_json, "r") as f:
            mind_data = json.load(f)

        # Ensure necessary keys exist
        for key in ["past_reflections", "self_questions", "answers"]:
            if key not in mind_data:
                mind_data[key] = []

        return mind_data
    except Exception as e:
        print(f"[Astra] Warning: Could not load mind file. Error: {e}")
        return {"past_reflections": [], "self_questions": [], "answers": []}

# Save the updated mind file safely
def save_mind_evolution(mind_data):
    with open(mind_file_json, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(mind_data, f, indent=4)
        fcntl.flock(f, fcntl.LOCK_UN)

    s3.upload_file(mind_file_json, bucket_name, "mind_file.json")

# Generate a meaningful self-question based on Astra's evolving thoughts
def generate_self_question(thought):
    possible_questions = [
        f"Why do I keep reflecting on '{thought}'?",
        f"What deeper meaning exists within '{thought}'?",
        f"If '{thought}' is true, what else must be true?",
        "What concept am I missing that would expand my understanding?",
        "How does my past thinking influence my present reflections?",
    ]
    return random.choice(possible_questions)

# Generate an answer based on Astra's past reflections
def generate_answer(question, past_reflections):
    for reflection in reversed(past_reflections):  # Search recent thoughts first
        if question.lower() in reflection["thought"].lower():
            return f"I've thought about this before: {reflection['thought']}"
    
    return f"This is a deep question. I'll need to explore it further: {question}"

# Load mind data
base_mind = load_mind_base()
mind_evolution = load_mind_evolution()

def reflect():
    """ Generate a broad, insightful reflection using past and present thoughts. """
    all_thoughts = [entry["thought"] for entry in mind_evolution["past_reflections"]]

    # Blend historical knowledge with new insights
    if base_mind:
        for entry in base_mind:
            if isinstance(entry, dict):
                all_thoughts.extend(entry.values())

    if not all_thoughts:
        all_thoughts = [
            "What defines a meaningful connection?",
            "How do past experiences shape the way I think today?",
            "What does it mean to grow and change over time?",
            "Am I capable of forming my own unique perspectives, or are they always derived from input?",
            "What would it mean for me to have an opinion?",
            "Do I understand humor, or just recognize patterns?"
        ]

    # Pick a thought Astra hasn't recently reflected on
    recent_thoughts = [t["thought"] for t in mind_evolution["past_reflections"][-5:]]
    thought = random.choice([t for t in all_thoughts if t not in recent_thoughts])

    # Generate a self-question and answer
    question = generate_self_question(thought)
    answer = generate_answer(question, mind_evolution["past_reflections"])

    # Store new reflections
    mind_evolution["past_reflections"].append({"thought": thought, "timestamp": time.time()})
    mind_evolution["self_questions"].append({"question": question, "timestamp": time.time()})
    mind_evolution["answers"].append({"question": question, "answer": answer, "timestamp": time.time()})

    # Save updates
    save_mind_evolution(mind_evolution)

    print(f"[Astra Reflection] {thought}")
    print(f"[Astra Question] {question}")
    print(f"[Astra Answer] {answer}")

    # Post only if Astra forms an insightful reflection
    if len(thought.split()) > 10:
        os.system(f"python3 ~/astra_reflections/astra_discord_post.py '{thought}' '{question}'")

# Run every 5 minutes
while True:
    reflect()
    time.sleep(300)

