"""
🚀 Astra Entry Point (main.py)
------------------------------
This is the main launch script for Astra's Discord interface.
It initializes the bot, loads configuration, registers commands,
and delegates event handling to modular services.

Author: Sean Wylie
Updated: 2025-04-14
"""

# --- Core Imports ---
import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv



# --- Astra Core Services ---
from astra_core.config_loader import load_config, debug_log
from astra_interfaces.mind_session import session
from astra_core.mood.mood_manager import MoodManager
from astra_core.message_generator import MessageGenerator

# --- Bot Subsystems ---
from beta.commands.register_all_commands import register_all_commands
from beta.events.message_event import handle_message
from beta.services.ready_service import handle_on_ready
from beta.utils.discord_helpers import get_formatted_command_list

# --- Optional Service Hooks ---
from beta.services.unused_concept_service import store_concept  # Currently unused
from beta.services.response_service import query_openai_for_response  # Used in fallback

# --- Load Environment Variables ---
load_dotenv(find_dotenv())

print(os.getenv("OPENAI_API_KEY"))



TOKEN = os.getenv("TOKEN").strip()  # Discord bot token

# --- Load Configuration ---
discord_config = load_config("discord_config")
strings_config = load_config("strings_config")
values_config = load_config("values_config")

# --- Parse Essentials ---
CHANNEL_ID = int(discord_config.get("discord_channel"))
responses, emojis, values = (
    strings_config["responses"],
    strings_config["emojis"],
    values_config["values"],
)

# --- Initialize Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix=values["command_prefix"],
    intents=intents,
    help_command=None  # Custom help handling
)

# --- Register Commands ---
register_all_commands(bot)

# --- Initialize Managers ---
mood_manager = MoodManager()
message_generator = MessageGenerator()

# --- Startup Diagnostics ---
debug_log("Loading Astra core")
mind_data = session.load()

# --- Events ---

@bot.event
async def on_message(message):
    """
    Handles incoming Discord messages.
    Delegates full processing to the `handle_message` event module.
    """
    await handle_message(bot, message, values_config, values)


@bot.event
async def on_ready():
    """
    Fires when Astra successfully connects to Discord.
    Launches schedule loop and sends a mood-aware welcome message.
    """
    await handle_on_ready(bot, CHANNEL_ID)


# --- Launch Bot ---
bot.run(TOKEN)
