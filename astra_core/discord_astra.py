import sys
import os
import random
import discord
from discord.ext import commands
import json

# Ensure the parent directory (astra_reflections) is added to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from astra_core.config_loader import load_config
from astra_core.processing import process_reflection

# Ensure the parent directory (astra_reflections) is added to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ✅ Load Discord configuration from discord_config.json
discord_config = load_config("discord_config")  # Discord bot token and channel ID

# Load the mind_file.json directly from the base directory
mind_file_path = "/home/ubuntu/astra_reflections/mind_file.json"

def load_mind_file():
    """Load the mind file from the correct path."""
    try:
        with open(mind_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"🚨 Mind file not found: {mind_file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"🚨 Error decoding the mind file: {mind_file_path}")
        return {}

# ✅ Load Astra's mind file (reflections and questions) from mind_file.json
mind_file = load_mind_file()

# Set up the bot and command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # Access the configured channel ID from the loaded config
    channel = bot.get_channel(int(discord_config["discord_channel"]))  # Use the channel from discord_config.json
    await channel.send(f"Hello, I am Astra! I am ready to learn and reflect with you!")

@bot.command()
async def reflect(ctx, *, topic: str = None):
    """Processes Astra's reflection and responds in Discord."""

    random_reflection = process_reflection()

    # ✅ Ensure message length is below 1500 characters
    if len(random_reflection) > 1500:
        random_reflection = random_reflection[:1497] + "..."  # ✅ Truncate long messages

    await ctx.send(f"Here’s a new reflection I generated: {random_reflection}")


    await ctx.send(f"Here’s a new reflection I generated: {random_reflection}")

@bot.command()  # Register the ask command
async def ask(ctx):
    """The ask command that Astra uses to ask a self-reflective question."""
    # Astra asks a self-reflective question from mind_file.json
    question = f"🤔 Why do you think this idea is important: {random.choice(mind_file['self_questions'])}?"
    await ctx.send(question)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Don't let Astra reply to itself

    # Handle other messages if needed
    await bot.process_commands(message)

# Run the bot using the token from the config
bot.run(discord_config["discord_token"])