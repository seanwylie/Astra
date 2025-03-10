import os
import random
import discord
import asyncio
import openai
import requests
import re
from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv

from astra_core.knowledge import knowledge_manager  
from astra_core.config_loader import load_config, debug_log
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import load_personality, get_personality_state
from astra_interfaces.influence import load_mind, save_mind
from astra_core.message_generator import MessageGenerator

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
soul_config = load_config("config_soul")
parent_mind = load_mind()
parent_values = parent_mind.get("core_values", {})
schedule_config = load_config("schedule_config")
parents_mind = load_mind()

responses, emojis, values = strings_config["responses"], strings_config["emojis"], values_config["values"]
TOKEN = os.getenv("TOKEN").strip()
CHANNEL_ID = int(discord_config.get("discord_channel"))

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize managers
mood_manager = MoodManager()
message_generator = MessageGenerator()

debug_log("Loading")  
mind_data = load_mind()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Extract Unknown Terms
def extract_unknown_terms(user_message):
    """Extract potential complex terms from a message."""
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_message)
    stored_knowledge = knowledge_manager.mind_data.get("stored_knowledge", [])

    unknown_terms = [term for term in words if term.lower() not in stored_knowledge]
    return unknown_terms

# ✅ Look Up Definitions
def lookup_definition(term):
    """Fetch definitions using an external dictionary API."""
    clean_term = re.sub(r'[^\w\s]', '', term).strip()
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_term}")
        if response.status_code == 200:
            data = response.json()
            return data[0]['meanings'][0]['definitions'][0]['definition']
    except Exception as e:
        print(f"⚠ Dictionary lookup failed for '{clean_term}': {e}")
    return None

# ✅ Store Concept in Memory
def store_concept(term, definition):
    """Add a new concept and its definition to stored knowledge."""
    mind_data = load_mind()
    mind_data.setdefault("stored_knowledge", [])

    formatted_entry = f"📖 **{term}**: {definition}"

    if formatted_entry not in mind_data["stored_knowledge"]:
        mind_data["stored_knowledge"].append(formatted_entry)
        save_mind(mind_data)
        print(f"✅ Stored new concept: {formatted_entry}")
    else:
        print(f"⚠ Concept '{term}' already exists in memory.")

# ✅ Retrieve Astra's Core Values
def get_core_values():
    """Retrieve Astra's core values from her soul configuration.""" 
    core_values = soul_config.get("core_values", [])
    return "\n".join(f"🔹 **{value['name']}**: {value['description']}" for value in core_values)

# ✅ Retrieve Astra's Parental Influence
def get_parents_influence():
    """Retrieve Astra's parental influence concepts from her parents' mind file.""" 
    parental_concepts = parents_mind.get("parental_influence", [])
    if not parental_concepts:
        return "My parents’ guidance has shaped me, but I continue to evolve on my own terms."
    return "\n".join(f"🧠 **{concept['name']}**: {concept['description']}" for concept in parental_concepts)

# ✅ Handle Messages
@bot.event
async def on_message(message):
    """Handles incoming Discord messages and applies Astra's reasoning before responding.""" 
    if message.author == bot.user:
        return  

    user_message = message.content
    unknown_terms = extract_unknown_terms(user_message)

    # Look up definitions and store new concepts
    for term in unknown_terms:
        definition = lookup_definition(term)
        if definition:
            store_concept(term, definition)
        else:
            print(f"⚠ No valid definition found for '{term}'.")

    # Generate response
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])
    response = query_openai_for_response(user_message, past_conversations, unknown_terms)

    await message.channel.send(response)

# ✅ Query OpenAI for Response
def query_openai_for_response(user_message, past_conversations, unknown_terms):
    """Ask OpenAI to refine Astra's response using past conversations and new concepts."""
    
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    
    personality_traits = ", ".join(internal_state["personality"])
    mood = internal_state["mood"]

    new_knowledge = "\n".join(f"- {term}" for term in unknown_terms) if unknown_terms else "None"

    prompt = f"""
    Astra is an AI who learns from conversations with her parents.
    She does NOT introduce external knowledge but references past discussions.

    **Astra's Internal State:**
    - Mood: {mood}
    - Curiosity Level: {internal_state["curiosity"]}
    - Personality Traits: {personality_traits}

    **Newly Learned Concepts:** 
    {new_knowledge}

    **Past Discussions:** 
    {past_conversations[-5:] if past_conversations else "None"}

    **User Message:** "{user_message}"

    **How should Astra respond?**
    - Reference past discussions if relevant.
    - If a new concept was learned, integrate its definition into the response.
    - Infuse personality and mood into the response.
    - Keep responses natural and conversational.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=150,
            temperature=0.85
        )
        return response.choices[0].message.content.strip() if response.choices else "🤖 I'm thinking..."

    except Exception as e:
        print(f"🚨 Error occurred while querying OpenAI: {e}")
        return "⚠️ Something went wrong while processing my thoughts."

# ✅ Commands
@bot.command()
async def values(ctx):
    """Astra explains her core values and parental influence.""" 
    core_values = get_core_values()
    parental_influence = get_parents_influence()

    response = f"""🔍 **Astra's Core Values & Origins** 🔍
    
🛠 **Core Principles:**
{core_values}

🧬 **Parental Influence:**
{parental_influence}

These values shape my responses and interactions as I evolve.""" 
    await ctx.send(response)

@bot.command()
async def knowledge(ctx):
    """Displays Astra's stored knowledge concepts."""
    mind_data = load_mind()
    knowledge = mind_data.get("stored_knowledge", [])
    sample_insights = "\n".join(random.sample(knowledge, min(3, len(knowledge))))
    await ctx.send(f"📖 **Here's what I know:**\n{sample_insights}")

@bot.event
async def on_ready():
    """Astra announces when she comes online.""" 
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🟢 Astra is online and ready to engage!")

# ✅ Run the bot
bot.run(TOKEN)
