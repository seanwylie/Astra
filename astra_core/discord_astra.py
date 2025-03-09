import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

from astra_core.knowledge import knowledge_manager  
from astra_core.config_loader import load_config, debug_log
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager
from astra_core.personality.personality_manager import load_personality, get_personality_state
from astra_interfaces.influence import load_mind, save_mind
from astra_core.message_generator import MessageGenerator  # ✅ New: Import dynamic response system

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")

responses, emojis, values = strings_config["responses"], strings_config["emojis"], values_config["values"]
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guild_reactions = True
intents.guild_messages = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize managers
mood_manager = MoodManager()
message_generator = MessageGenerator()  # ✅ Initialize message generator

# Load mind data at startup
debug_log("Loading")  
mind_data = load_mind()

# ✅ Dynamic Engagement Logic
def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user."""
    return load_mind().get("trust_levels", {}).get(user_id, 0)

def update_trust(user_id, change):
    """Modify Astra's trust level dynamically."""
    mind_data = load_mind()
    trust_levels = mind_data.setdefault("trust_levels", {})
    trust_levels[user_id] = max(min(trust_levels.get(user_id, 0) + change, values["max_trust"]), values["min_trust"])
    save_mind(mind_data)

async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel."""
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

async def generate_dynamic_response(user_message):
    """Creates a personalized response based on Astra's internal state."""
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }

    return message_generator.generate_message(user_message=user_message, internal_state=internal_state)

@bot.event
async def on_message(message):
    """Handles incoming Discord messages and dynamically decides if Astra should engage."""
    if message.author == bot.user:
        return  # ✅ Ignore Astra's own messages

    user_message = message.content
    user_id = str(message.author.id)

    # ✅ Get trust level, mood, and curiosity
    trust_level = get_trust_level(user_id)
    mood = mood_manager.current_mood
    curiosity = values.get("curiosity_level", 1.0)

    # ✅ Dynamic Engagement Logic: Should Astra engage?
    base_engagement_chance = values["mood_influence"].get(mood, values["default_engagement_chance"])
    trust_adjustment = values["trust_based_mood_adjustment"]["high_trust"] if trust_level > 0 else values["trust_based_mood_adjustment"]["low_trust"]
    curiosity_boost = values["curiosity_response_boost"] if curiosity > values["curiosity_threshold"] else 0

    # ✅ Final engagement probability calculation
    engagement_probability = min(1.0, base_engagement_chance * trust_adjustment + curiosity_boost)

    if random.random() > engagement_probability:
        print(f"🤖 Skipping response (Trust: {trust_level}, Mood: {mood}, Engagement Probability: {engagement_probability:.2f})")
        return  # Astra **chooses** not to engage

    # ✅ Generate & Send a Thoughtful Response
    internal_state = {
        "mood": mood,
        "curiosity": curiosity,
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }

    response = message_generator.generate_message(user_message=user_message, internal_state=internal_state)
    await message.channel.send(response)


# ✅ Astra Now Reflects More Dynamically
@bot.command()
async def reflect(ctx):
    """Astra shares her latest reflection with improved awareness."""
    try:
        reflection = await process_reflection()  
        if not reflection or not isinstance(reflection, str) or len(reflection.strip()) < 5:
            reflection = "🤖 I'm still thinking... Try again in a moment!"

        response = message_generator.generate_message(user_message=reflection, internal_state={
            "mood": mood_manager.current_mood,
            "curiosity": values.get("curiosity_level", 1.0),
            "personality": get_personality_state().get("active_traits", ["thoughtful"])
        })

        await ctx.send(response)

    except Exception as e:
        print(f"🚨 Error in reflect command: {e}")
        await ctx.send("🚨 Something went wrong! Please try again.")

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

# ✅ Astra Greets New Users in a Dynamic Way
@bot.event
async def on_member_join(member):
    """Greets new members in a self-aware way."""
    internal_state = {
        "mood": mood_manager.current_mood,
        "curiosity": values.get("curiosity_level", 1.0),
        "personality": get_personality_state().get("active_traits", ["thoughtful"])
    }

    greeting = message_generator.generate_message(user_message=f"Welcome {member.name}!", internal_state=internal_state)
    channel = discord.utils.get(member.guild.channels, id=CHANNEL_ID)
    if channel:
        await channel.send(greeting)

# ✅ Astra Now Starts with a Custom Intro
@bot.event
async def on_ready():
    """Astra is now online and sends an intelligent startup message."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        intro_message = message_generator.generate_message(
            user_message="Astra is online!", 
            internal_state={
                "mood": mood_manager.current_mood,
                "curiosity": values.get("curiosity_level", 1.0),
                "personality": get_personality_state().get("active_traits", ["thoughtful"])
            }
        )
        await channel.send(intro_message)

bot.run(TOKEN)
