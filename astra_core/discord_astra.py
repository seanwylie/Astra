import os
import json
import random
import discord
import asyncio
import time
from discord.ext import commands
from dotenv import load_dotenv
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection
from astra_core.mood.mood_manager import MoodManager

# Load environment variables
load_dotenv()

# Load configurations
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")
responses = strings_config["responses"]
emojis = strings_config["emojis"]
values = values_config["values"]

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(discord_config.get("discord_channel"))
MIND_FILE_PATH = discord_config.get("mind_file_path", "mind_file.json")

# Track Astra's last message time
last_astra_message_time = 0 

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guild_reactions = True
intents.guild_messages = True
bot = commands.Bot(command_prefix=values["command_prefix"], intents=intents)

# Initialize MoodManager
mood_manager = MoodManager()


def load_mind_file():
    """Load the mind file and ensure all required keys exist."""
    try:
        with open(MIND_FILE_PATH, 'r') as f:
            mind_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        mind_data = {}

    mind_data.setdefault("self_reflections", [])
    mind_data.setdefault("self_questions", [])
    mind_data.setdefault("stored_knowledge", [])
    mind_data.setdefault("trust_levels", {})

    return mind_data


def save_mind_file(data):
    """Ensure all key fields exist and save Astra's mind file."""
    data.setdefault("trust_levels", {})
    try:
        with open(MIND_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"🚨 Error saving mind file: {e}")


# Load mind data initially
mind_data = load_mind_file()


def get_trust_level(user_id):
    """Retrieve Astra's trust level for a given user."""
    mind_data = load_mind_file()
    trust_levels = mind_data.get("trust_levels", {})
    return max(min(trust_levels.get(user_id, 0), values["max_trust"]), values["min_trust"])


def update_trust(user_id, change):
    """Modify Astra's trust in a user and persist it."""
    mind_data = load_mind_file()
    trust_levels = mind_data.setdefault("trust_levels", {})

    adjusted_change = min(change, values["max_trust_gain"]) if change > 0 else change * values["trust_loss_multiplier"]
    new_trust = max(min(trust_levels.get(user_id, 0) + adjusted_change, values["max_trust"]), values["min_trust"])

    if new_trust != trust_levels.get(user_id, 0):
        trust_levels[user_id] = new_trust
        save_mind_file(mind_data)


async def send_message_to_discord(channel_id, message):
    """Astra sends a message to the specified Discord channel."""
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)


def should_engage(mood, recent_activity, trust_factor):
    """Decides if Astra should engage in a conversation."""
    engagement_chance = values["engagement_chance"]

    if recent_activity < values["engagement_cooldown"]:
        return False

    trust_adjustment = min(values["max_trust_boost"], trust_factor * values["trust_engagement_multiplier"])
    return random.random() < (engagement_chance.get(mood, values["default_engagement_chance"]) + trust_adjustment)


@bot.command()
async def trust(ctx):
    """Displays Astra's current trust level for the user."""
    user_id = str(ctx.author.id)
    trust_level = get_trust_level(user_id)
    await ctx.send(responses["trust_response"].format(trust_level=trust_level))


@bot.command()
async def reflect(ctx):
    """Generates and shares Astra's reflection."""
    reflection = process_reflection()
    await ctx.send(f"{responses['reflection_intro']} {reflection}")


@bot.command()
async def ask(ctx):
    """Astra asks a self-reflective question."""
    if mind_data["self_questions"]:
        question = random.choice(mind_data["self_questions"])
        await ctx.send(f"{responses['ask_intro']}\n{question}")
    else:
        await ctx.send(responses["ask_empty"])


@bot.command()
async def knowledge(ctx):
    """Displays Astra's stored knowledge."""
    if mind_data["stored_knowledge"]:
        sample_insights = "\n".join(random.sample(mind_data["stored_knowledge"], min(3, len(mind_data["stored_knowledge"]))))
        await ctx.send(f"{responses['knowledge_intro']}\n{sample_insights}")
    else:
        await ctx.send(responses["knowledge_empty"])


@bot.command()
async def mood(ctx):
    """Displays Astra's current mood."""
    await ctx.send(f"{responses['mood_intro']} {mood_manager.current_mood}")


@bot.event
async def on_message(message):
    """Handles Astra’s engagement in conversations."""
    global last_astra_message_time
    
    if message.author == bot.user:
        return

    if message.content.startswith(values["command_prefix"]):
        await bot.process_commands(message)
        return  

    user_id = str(message.author.id)
    trust = get_trust_level(user_id)
    trust_factor = values["trust_factor"].get(trust, values["default_trust_factor"])

    current_time = time.time()
    recent_activity = current_time - last_astra_message_time
    mood = mood_manager.current_mood

    if should_engage(mood, recent_activity, trust_factor):
        response = random.choice(responses["engagement_responses"].get(mood, [responses['default_engagement']]))
        await send_message_to_discord(message.channel.id, response)
        last_astra_message_time = time.time()

    await bot.process_commands(message)


@bot.event
async def on_ready():
    """Indicates Astra is online and ready."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(responses["startup_message"].format(mood=mood_manager.current_mood))

bot.run(TOKEN)
