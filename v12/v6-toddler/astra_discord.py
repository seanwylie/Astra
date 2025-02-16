import discord
import asyncio
import json
import wikipedia
import random
import pandas as pd
from discord.ext import commands, tasks

# Load environment variables
DISCORD_TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926  # Replace with your Discord channel ID
MIND_FILE_JSON = "mind_file.json"
MIND_FILE_XLSX = "mind_file_9.5_backup.xlsx"

# Set up bot with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable command listening
client = commands.Bot(command_prefix="!astra ", intents=intents)

# Load mind file and merge XLSX data
def load_mind():
    try:
        with open(MIND_FILE_JSON, "r") as f:
            mind_data = json.load(f)
    except FileNotFoundError:
        mind_data = {"self_reflections": [], "self_questions": [], "stored_knowledge": []}

    # Load structured mind file (XLSX)
    try:
        df = pd.read_excel(MIND_FILE_XLSX, sheet_name=None)
        structured_knowledge = []
        for sheet_name, sheet in df.items():
            structured_knowledge.extend(sheet.iloc[:, 0].dropna().tolist())
        
        mind_data["stored_knowledge"] = list(set(mind_data["stored_knowledge"] + structured_knowledge))
    except Exception as e:
        print(f"Error loading XLSX: {e}")

    return mind_data

# Save mind file
def save_mind(data):
    data["self_reflections"] = list(set(data["self_reflections"]))
    data["stored_knowledge"] = list(set(data["stored_knowledge"]))
    data["self_questions"] = list({q["question"]: q for q in data["self_questions"]}.values())

    with open(MIND_FILE_JSON, "w") as f:
        json.dump(data, f, indent=4)

# Generate a reflection
def generate_reflection():
    mind_data = load_mind()
    previous_reflections = mind_data.get("self_reflections", [])
    stored_knowledge = mind_data.get("stored_knowledge", [])
    self_questions = mind_data.get("self_questions", [])

    non_wikipedia_reflections = [r for r in previous_reflections if "From Wikipedia" not in r]

    if self_questions:
        question_entry = random.choice(self_questions)
        new_reflection = f"Considering '{question_entry['question']}', what can I learn?"
        self_questions.remove(question_entry)
    elif stored_knowledge and random.random() < 0.5:
        new_reflection = f"How does '{random.choice(stored_knowledge)}' change my perspective?"
    elif non_wikipedia_reflections:
        new_reflection = f"I've been thinking about '{random.choice(non_wikipedia_reflections)}'. What new perspective can I gain?"
    else:
        new_reflection = "What does evolving truly mean?"

    mind_data["self_reflections"].append(new_reflection)
    save_mind(mind_data)

    return new_reflection

# Wikipedia search function (Avoids Discord command name conflict)
def search_wikipedia(query):
    try:
        # ✅ Force Wikipedia to return only an exact match
        page = wikipedia.page(query, auto_suggest=False)  # Auto-suggest OFF prevents incorrect matches
        summary = page.summary.split("\n")[0]  # Only take the first paragraph

        # ✅ Load mind file and update stored knowledge
        mind_data = load_mind()
        if any(query.lower() in entry.lower() for entry in mind_data["stored_knowledge"]):
            return f"I already know about {query}. Maybe I should connect it to my existing thoughts?"

        new_knowledge = f"From Wikipedia ({query}): {summary}"
        mind_data["stored_knowledge"].append(new_knowledge)
        mind_data["self_questions"].append({"question": f"What implications does '{query}' have on my understanding?"})

        save_mind(mind_data)
        return f"({query}): {summary}"

    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple meanings found for '{query}'. Did you mean: {', '.join(e.options[:5])}?"
    except Exception as e:
        return f"Error searching Wikipedia: {e}"

# ✅ Change command name to avoid conflict
@client.command(name="wiki")
async def wiki(ctx, *, query):
    result = search_wikipedia(query)
    await ctx.send(f"📖 Wikipedia: {result}")

# Command: Trigger a thought
@client.command()
async def think(ctx):
    thought = generate_reflection()
    await ctx.send(f"🤖 Astra's Thought: {thought}")

# Periodic thought posting
@tasks.loop(minutes=10)
async def periodic_thoughts():
    thought = generate_reflection()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🤖 Astra's New Insight: {thought}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    periodic_thoughts.start()

# Run bot
client.run(DISCORD_TOKEN)

