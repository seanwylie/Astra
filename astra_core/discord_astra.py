import os
import random
import discord
import openai
import asyncio
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
schedule_config = load_config("schedule_config")

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

# Load mind data at startup
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
    """Handles incoming Discord messages and applies OpenAI reasoning before responding."""
    if message.author == bot.user:
        return  # Ignore Astra's own messages

    user_message = message.content
    user_id = str(message.author.id)

    # Store the conversation
    knowledge_manager.store_conversation(f"{message.author.name}: {user_message}")
    past_conversations = knowledge_manager.mind_data.get("past_conversations", [])

    # OpenAI Refinement (ONLY for rewording, not injecting new knowledge)
    thoughtful_response = query_openai_for_response(user_message, past_conversations)

    if thoughtful_response:
        response = thoughtful_response
    else:
        response = message_generator.generate_message(
            user_message=user_message, 
            internal_state={
                "mood": mood_manager.current_mood,
                "curiosity": values.get("curiosity_level", 1.0),
                "personality": get_personality_state().get("active_traits", ["thoughtful"])
            },
            past_conversations=past_conversations
        )

    await message.channel.send(response)

def query_openai_for_response(user_message, past_conversations):
    """Ask OpenAI to refine Astra's response using past conversations, personality, and mood."""
    
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }
    
    personality_traits = ", ".join(internal_state["personality"])
    mood = internal_state["mood"]

    prompt = f"""
    Astra is an AI who has ongoing discussions and learns from them.
    She does NOT introduce external knowledge but references past conversations.

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

    response = openai.OpenAI().chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=150,
        temperature=0.85  # 🔥 Make Astra more expressive!
    )

    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    else:
        return None

# ✅ Astra Reflects
@bot.command()
async def reflect(ctx):
    """Astra shares her latest reflection with improved awareness."""
    reflection = await process_reflection()  
    if not reflection or not isinstance(reflection, str) or len(reflection.strip()) < 5:
        reflection = "🤖 I'm still thinking... Try again in a moment!"

    response = message_generator.generate_message(
        user_message=reflection,
        internal_state={
            "mood": mood_manager.current_mood,
            "curiosity": values.get("curiosity_level", 1.0),
            "personality": get_personality_state().get("active_traits", ["thoughtful"])
        }
    )
    await ctx.send(response)

# ✅ Astra Asks Thoughtful Questions
@bot.command()
async def ask(ctx):
    """Astra asks a reflective question based on mood."""
    if mind_data["self_questions"]:
        question_entry = random.choice(mind_data["self_questions"])
        question_text = question_entry["question"] if isinstance(question_entry, dict) else question_entry
    else:
        question_text = "I don't have a question right now. Ask me to reflect!"

    await ctx.send(f"{responses['ask_intro'].get(mood_manager.current_mood, 'Hmm...')}\n{question_text}")

# ✅ Astra Displays Knowledge
@bot.command()
async def knowledge(ctx):
    """Displays Astra's stored knowledge."""
    mind_data = load_mind()
    sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
    await ctx.send(f"📖 **Here's what I know:**\n{sample_insights}")

# ✅ Astra Reports Her Mood
@bot.command()
async def mood(ctx):
    """Reports Astra's current mood dynamically."""
    mood = mood_manager.current_mood
    await ctx.send(f"🧠 I'm feeling {mood} today.")

# ✅ Astra Greets New Users
@bot.event
async def on_member_join(member):
    """Greets new members dynamically."""
    greeting = message_generator.generate_message(user_message=f"Welcome {member.name}!", internal_state={
        "mood": mood_manager.current_mood,
        "curiosity": values.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    })
    channel = discord.utils.get(member.guild.channels, id=CHANNEL_ID)
    if channel:
        await channel.send(greeting)

# ✅ Astra Sends a Startup Message
@bot.event
async def on_ready():
    """Astra announces when she comes online."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🟢 Astra is online and ready to engage!")

bot.run(TOKEN)
