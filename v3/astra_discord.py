import discord
import asyncio
import json
import wikipedia
import random

TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926
mind_file_path = "mind_file.json"

# Load mind file
def load_mind():
    try:
        with open(mind_file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"self_reflections": [], "self_questions": []}

# Save mind file
def save_mind(mind_data):
    with open(mind_file_path, "w") as f:
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

# Initialize Discord client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Handle messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!astra"):
        command = message.content[len("!astra"):].strip()

        if command.lower().startswith("wikipedia"):
            query = command[len("wikipedia"):].strip()
            if query:
                response = search_wikipedia(query)
            else:
                response = "Please provide a topic to search."

        elif command.lower().startswith("think"):
            mind_data = load_mind()
            if mind_data["self_reflections"]:
                response = f"🤖 Astra's Thought: {random.choice(mind_data['self_reflections'])}"
            else:
                response = "I'm still processing new thoughts."

        elif command.lower().startswith("ask"):
            new_question = command[len("ask"):].strip()
            mind_data = load_mind()
            mind_data["self_questions"].append({"question": new_question})
            save_mind(mind_data)
            response = f"🤖 Question recorded: {new_question}"

        else:
            response = "🤖 Command not recognized. Try `!astra think` or `!astra wikipedia [topic]`."

        await message.channel.send(response)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

client.run(TOKEN)

