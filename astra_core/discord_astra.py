import os
import random
import discord
import asyncio


import openai
from openai import OpenAI  # We need to use the new `OpenAI` client


from discord.ext import commands
from dotenv import load_dotenv

from astra_core.knowledge import knowledge_manager  
from astra_core.config_loader import load_config, debug_log
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import load_personality, get_personality_state
from astra_interfaces.influence import load_mind, save_mind
from astra_core.message_generator import MessageGenerator


openai.api_key = os.getenv("OPENAI_API_KEY")

# Instantiate the client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
soul_config = load_config("config_soul")  # Load core values dynamically
parent_mind = load_mind()  # Load mind file from S3 (mind_file_parents.json)
parent_values = parent_mind.get("core_values", {})  # Retrieve core values from S3
schedule_config = load_config("schedule_config")
parents_mind = load_mind()  # Load Astra's parental influence

responses, emojis, values = strings_config["responses"], strings_config["emojis"], values_config["values"]
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize managers
mood_manager = MoodManager()
message_generator = MessageGenerator()

# Initialize OpenAI Client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

debug_log("Loading")  
mind_data = load_mind()

# ✅ Trust System
def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user."""
    return load_mind().get("trust_levels", {}).get(user_id, 0)

def update_trust(user_id, change):
    """Modify Astra's trust level dynamically."""
    mind_data = load_mind()
    trust_levels = mind_data.setdefault("trust_levels", {})
    trust_levels[user_id] = max(min(trust_levels.get(user_id, 0) + change, values["max_trust"]), values["min_trust"])
    save_mind(mind_data)

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

# ✅ Send Message Function
async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel.""" 
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

# ✅ Generate Dynamic Response
async def generate_dynamic_response(user_message):
    """Creates a personalized response based on Astra's internal state.""" 
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    return message_generator.generate_message(user_message=user_message, internal_state=internal_state)

# ✅ Handle Messages
@bot.event
async def on_message(message):
    """Handles incoming Discord messages and applies Astra's reasoning before responding.""" 
    if message.author == bot.user:
        return  # Ignore Astra's own messages

    user_message = message.content.lower()

    # Load Astra's core values from both sources
    soul_config = load_config("config_soul")  
    parent_mind = load_mind()
    parent_values = parent_mind.get("core_values", [])
    parent_insights = parent_mind.get("insights", [])

    # Merge `config_soul.json` and `mind_file_parents.json`
    soul_principles = soul_config.get("core_values", [])
    combined_values = soul_principles + parent_values  # Merge local + S3 values

    # **Explicitly handle core value questions**
    if "core values" in user_message or "what do you believe" in user_message or "what are your values" in user_message:
        if combined_values:
            formatted_values = "\n".join(
                f"**{value['name']}**: {value['description']}" for value in combined_values
            )
            response = f"🧠 **Astra's Core Values:**\n{formatted_values}"
        else:
            response = "⚠️ I wasn't able to retrieve my core values. Something might be missing in my soul configuration."

        await message.channel.send(response)
        return  # No need to process further

    # Handle Astra’s beliefs & philosophical insights
    if "what do you think" in user_message or "what is your philosophy" in user_message:
        formatted_insights = "\n".join(f"📌 {insight['insight']}" for insight in parent_insights[:5])
        response = f"🧠 **Astra's Perspective:**\n{formatted_insights}"
        await message.channel.send(response)
        return  # No need to process further

    # Store the conversation
    knowledge_manager.store_conversation(f"{message.author.name}: {message.content}")

    # Retrieve past conversations for context
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])

    # Generate Astra's Response (Either OpenAI-assisted or internal)
    response = query_openai_for_response(user_message, past_conversations)
    if not response:
        response = message_generator.generate_message(
            user_message=user_message, 
            internal_state={
                "mood": mood_manager.current_mood,
                "curiosity": values.get("curiosity_level", 1.0),
                "personality": get_personality_state().get("active_traits", ["thoughtful"])
            },
            past_conversations=past_conversations
        )

    # If response is still empty, provide a fallback
    response = response or "🤖 I'm thinking... but I might need a moment!"

    await message.channel.send(response)



def query_openai_for_response(user_message, past_conversations):
    """Ask OpenAI to refine Astra's response using past conversations, personality, and mood."""
    
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values_config.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    
    personality_traits = ", ".join(internal_state["personality"])
    mood = internal_state["mood"]

    prompt = f"""
    Astra is an AI who learns from conversations with her parents.
    She does NOT introduce external knowledge but references past discussions.

    **Astra's Internal State:**
    - Mood: {mood}
    - Curiosity Level: {internal_state["curiosity"]}
    - Personality Traits: {personality_traits}

    **Past Discussions:** 
    {past_conversations[-5:] if past_conversations else "None"}

    **User Message:** "{user_message}"

    **How should Astra respond?**
    - Reference past discussions if relevant.
    - Infuse personality and mood into the response.
    - Avoid generic AI disclaimers like "I don't have feelings."
    - Engage in the topic instead of just explaining facts.
    - Keep responses natural and conversational.
    """

    try:
        # Using the new OpenAI API client to get the response
        response = client.chat.completions.create(
            model="gpt-4",  # You can also use "gpt-3.5-turbo" or other available models
            messages=[{"role": "system", "content": prompt}],
            max_tokens=150,
            temperature=0.85  # Astra expresses herself more dynamically
        )

        # If there is a response, return it
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return None

    except openai.OpenAIError as e:
        # Handle OpenAI errors gracefully
        print(f"🚨 OpenAI error occurred: {e}")
        return None
    except Exception as e:
        print(f"🚨 Error occurred while querying OpenAI: {e}")
        return None


# Astra Explains Her Core Values & Parental Influence
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

@bot.event
async def on_ready():
    """Astra announces when she comes online.""" 
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🟢 Astra is online and ready to engage!")

# Ensure the token is valid and clean before running the bot
TOKEN = os.getenv("TOKEN").strip()
TOKEN = TOKEN.replace("{", "").replace("}", "")  # Ensure token format is clean
if not TOKEN:
    print("⚠️ Token is empty or improperly formatted. Please check the .env file.")
else:
    print(f"Token is valid and properly formatted.")

bot.run(TOKEN)
