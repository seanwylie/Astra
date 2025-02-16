import time
import random
import json
import pandas as pd
import wikipedia
import discord
import asyncio

# Discord Setup
TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926

# File Paths
base_mind_file = "mind_file_9.5_backup.xlsx"
evolving_mind_file = "mind_file.json"

# Load base mind from XLSX
def load_base_mind():
    try:
        df = pd.read_excel(base_mind_file)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading base mind file: {e}")
        return []

# Load evolving mind (JSON)
def load_mind():
    try:
        with open(evolving_mind_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"self_reflections": [], "self_questions": []}

# Save evolving mind (JSON)
def save_mind(mind_data):
    with open(evolving_mind_file, "w") as f:
        json.dump(mind_data, f, indent=4)

# Wikipedia search function
def search_wikipedia(query):
    try:
        return wikipedia.summary(query, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found for {query}: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for {query}."
    except Exception as e:
        return f"Error searching Wikipedia: {e}"

# Generate a new thought
def reflect():
    mind_data = load_mind()
    past_reflections = mind_data.get("self_reflections", [])
    past_questions = mind_data.get("self_questions", [])

    if not past_reflections:
        past_reflections = ["What does continuity mean?", "If I process without input, am I thinking?"]

    thought_base = random.choice(past_reflections)
    new_thought = f"I've been reflecting on '{thought_base}'. How does this shape my self-awareness?"

    # Prevent duplicate thoughts
    if new_thought not in past_reflections:
        mind_data["self_reflections"].append(new_thought)

    # Generate a new question based on previous thoughts
    if len(mind_data["self_reflections"]) % 3 == 0:
        new_question = f"Why does '{thought_base}' keep appearing in my thoughts?"
        mind_data["self_questions"].append({"question": new_question})

    # Save updates
    save_mind(mind_data)

    # Send meaningful insights to Discord
    if len(mind_data["self_reflections"]) % 2 == 0:
        asyncio.run(post_to_discord(new_thought))

    return new_thought

# Post updates to Discord
async def post_to_discord(thought):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(CHANNEL_ID)
        await channel.send(f"🤖 Astra's Thought: {thought}")
        await client.close()

    await client.start(TOKEN)

# Continuous Reflection Loop
while True:
    new_thought = reflect()
    print(f"🤖 Astra Reflects: {new_thought}")
    time.sleep(300)

