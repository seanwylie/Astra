"""
Astra: single entry point.
Unified app (no beta/core split). Config and logging set up first.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure project root is on path when running as script or module
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load env before app imports that use it
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
load_dotenv(os.path.expanduser("~/.env"))

# Configure logging first (no print override)
from app.logging_config import setup_logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), console=True)

logger = logging.getLogger("astra.main")

import discord
from discord.ext import commands

from app.config.loader import config_manager, debug_log
from app.interfaces.mind_session import session
from app.core.mood.mood_manager import MoodManager
from app.core.message_generator import MessageGenerator
from app.commands.register_all_commands import register_all_commands
from app.events.message_event import handle_message
from app.services.ready_service import handle_on_ready


def load_environment() -> str:
    """Load and validate environment variables."""
    required = {
        "TOKEN": "Discord bot token",
        "OPENAI_API_KEY": "OpenAI API key",
        "AWS_ACCESS_KEY_ID": "AWS access key",
        "AWS_SECRET_ACCESS_KEY": "AWS secret key",
    }
    missing = [var for var, _ in required.items() if not os.getenv(var)]
    if missing:
        logger.error("Missing required env: %s", missing)
        sys.exit(1)
    if not os.getenv("S3_BUCKET_NAME"):
        os.environ["S3_BUCKET_NAME"] = "swylie-astra"
        logger.info("Using default S3_BUCKET_NAME: swylie-astra")
    return os.getenv("TOKEN", "").strip()


def initialize_bot():
    """Initialize Discord bot from config."""
    discord_config = config_manager.get_discord_config()
    values_config = config_manager.get_values_config()
    if not discord_config or not values_config:
        logger.error("Failed to load required config (discord_config, values_config)")
        sys.exit(1)
    values = values_config.get("values", {})
    prefix = values.get("command_prefix", "!")
    channel_id = discord_config.get("discord_channel")
    if not channel_id:
        logger.error("discord_channel not set in config")
        sys.exit(1)
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
    return bot, int(channel_id), values_config


def setup_event_handlers(bot, channel_id, values_config):
    """Attach Discord event handlers."""

    @bot.event
    async def on_message(message):
        try:
            await handle_message(
                bot, message, values_config, values_config.get("values", {})
            )
        except Exception as e:
            logger.exception("Error handling message: %s", e)

    @bot.event
    async def on_ready():
        try:
            await handle_on_ready(bot, channel_id)
            from app.services.schedule_service import start_schedule
            await start_schedule(bot, channel_id)
            logger.info("Automated schedule started")
        except Exception as e:
            logger.exception("Error in on_ready: %s", e)

    @bot.event
    async def on_error(event, *args, **kwargs):
        logger.error("Discord error in %s: %s", event, args)


def main() -> None:
    try:
        logger.info("Starting Astra...")
        token = load_environment()
        bot, channel_id, values_config = initialize_bot()
        logger.info("Registering commands...")
        register_all_commands(bot)
        setup_event_handlers(bot, channel_id, values_config)
        MoodManager()
        MessageGenerator()
        debug_log("Loading Astra core", "general")
        session.load()
        logger.info("Astra initialized successfully")
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Shutting down Astra...")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
