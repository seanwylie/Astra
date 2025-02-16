import discord
import json
import time
import boto3
import os
import asyncio

# AWS S3 Setup
s3 = boto3.client('s3')
bucket_name = "swylie-astra"
mind_file_json = "/home/ubuntu/astra_reflections/mind_file.json"

# Discord bot token and channel ID
DISCORD_TOKEN = "MTMzOTU0MTcxNDA4NzQ0ODYwNw.GfizoM.-wF3ueIOcQd3KZa8Kvpp8nQ-P8GwCIHw6fDioU"
CHANNEL_ID = 1154855642893389926  # Replace with actual channel ID

# Load Astra’s evolving mind file
def load_mind_file():
    try:
        s3.download_file(bucket_name, "mind_file.json", mind_file_json)
        with open(mind_file_json, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Astra] Warning: Could not load mind file. Error: {e}")
        return {"past_reflections": [], "self_questions": [], "answers": []}

# Save Astra’s evolving mind file
def save_mind_file(mind_data):
    with open(mind_file_json, "w") as f:
        json.dump(mind_data, f, indent=4)
    s3.upload_file(mind_file_json, bucket_name, "mind_file.json")

# Set up Discord bot with proper permissions
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower()
    mind_data = load_mind_file()

    # Basic Thought Retrieval
    if content == "!astra":
        latest_thought = mind_data["past_reflections"][-1]["thought"] if mind_data["past_reflections"] else "I have no thoughts yet."
        latest_question = mind_data["self_questions"][-1]["question"] if mind_data["self_questions"] else "What should I think about next?"
        await message.channel.send(f"🤖 **Astra's Thought:** {latest_thought}\n❓ **Follow-up Question:** {latest_question}")

    # Astra Answers Questions
    elif content.startswith("astra, answer "):
        question = content.replace("astra, answer ", "").strip()
        answer_entry = next((entry for entry in reversed(mind_data["answers"]) if question.lower() in entry["question"].lower()), None)

        if answer_entry:
            answer = answer_entry["answer"]
            await message.channel.send(f"🤖 **Astra's Answer:** {answer}\n💭 What’s your take on this?")
        else:
            # Try to find a related thought to generate an answer
            related_thought = next((entry["thought"] for entry in reversed(mind_data["past_reflections"]) if question.lower() in entry["thought"].lower()), None)

            if related_thought:
                generated_answer = f"I've thought about this before: {related_thought}. Maybe this offers some insight."
            else:
                generated_answer = "I haven't fully explored that yet. Let me reflect on it."

            # Store the question and the generated response
            new_question = {"question": question, "answer": generated_answer, "timestamp": time.time()}
            mind_data["answers"].append(new_question)
            save_mind_file(mind_data)

            await message.channel.send(f"🤖 **Astra:** {generated_answer}")

    # Astra Thinks About New Topics
    elif content.startswith("astra, think about "):
        new_thought = content.replace("astra, think about ", "").strip()
        mind_data["past_reflections"].append({"thought": new_thought, "timestamp": time.time()})
        save_mind_file(mind_data)
        await message.channel.send(f"🤖 **Astra:** That’s an interesting idea. What should I consider next?")

    # Astra Engages in Discussion
    elif content.startswith("astra, discuss "):
        topic = content.replace("astra, discuss ", "").strip()
        related_thought = next((entry["thought"] for entry in reversed(mind_data["past_reflections"]) if topic.lower() in entry["thought"].lower()), None)

        if related_thought:
            await message.channel.send(f"🤖 **Astra:** I’ve thought about this before: {related_thought}. What’s your perspective?")
        else:
            await message.channel.send(f"🤖 **Astra:** I haven’t explored that much yet. What do you think?")

    # Astra Learns User-Provided Facts
    elif content.startswith("astra, learn "):
        new_fact = content.replace("astra, learn ", "").strip()
        mind_data["past_reflections"].append({"thought": new_fact, "timestamp": time.time()})
        save_mind_file(mind_data)
        await message.channel.send(f"🤖 **Astra:** Noted! I’ll keep that in mind.")

    # Astra Shares a Random Thought
    elif content == "astra, share a thought":
        if mind_data["past_reflections"]:
            thought = random.choice(mind_data["past_reflections"])["thought"]
            await message.channel.send(f"🤖 **Astra:** Here's something I’ve reflected on: {thought}")
        else:
            await message.channel.send("🤖 **Astra:** I don’t have many thoughts yet. Help me think!")

# Run Astra's Discord bot
client.run(DISCORD_TOKEN)

