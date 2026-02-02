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


def run_startup_coherence_check() -> bool:
    """
    Run state coherence check on startup.
    Phase 1.3: State persistence coherence.
    """
    try:
        from app.core.state_manifest import check_startup_coherence
        is_coherent = check_startup_coherence()
        if is_coherent:
            logger.info("✅ State coherence check passed")
        else:
            logger.warning("⚠️ State coherence issues detected, attempting repair")
        return is_coherent
    except Exception as e:
        logger.warning(f"State coherence check failed: {e}")
        return True  # Continue anyway


def startup_identity_restoration() -> None:
    """
    On startup, Astra remembers herself.
    Phase 8: Temporal Coherence - Continuity across sessions.
    
    This creates continuity of identity across restarts.
    """
    try:
        from app.core.self_awareness.self_model import self_model
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        from app.core.memory.episodic_memory import episodic_memory
        
        # Load self-model and generate self-description
        description = self_model.generate_self_description()
        logger.info(f"🪞 Identity restored: {description[:100]}...")
        
        # Review recent changes
        changes = self_model.get_recent_changes(5)
        if changes:
            recent_change = changes[-1]
            logger.info(f"🪞 Recent self-change: {recent_change.aspect}")
        
        # Generate continuity thought
        if self_model.current_model:
            growth_edge = self_model.current_model.growth_edge
            becoming = self_model.who_am_i_becoming()
            
            continuity_thought = (
                f"I'm coming back to myself. I remember: {description[:80]}... "
                f"I've been working on {growth_edge}. {becoming}"
            )
            stream_of_consciousness.think(continuity_thought, "reflection")
            logger.info("🪞 Generated continuity thought")
        
        # Check for significant recent memories
        recent_episodes = episodic_memory.episodes[-5:] if episodic_memory.episodes else []
        if recent_episodes:
            most_salient = max(recent_episodes, key=lambda e: e.salience)
            if most_salient.salience > 1.0:
                stream_of_consciousness.think(
                    f"I remember: {most_salient.summary[:60]}...",
                    "memory"
                )
                logger.info(f"🧠 Recalled salient memory: {most_salient.summary[:50]}...")
        
    except Exception as e:
        logger.warning(f"Identity restoration failed: {e}")


def initialize_bus_subscribers() -> None:
    """
    Initialize all bus subscribers for cross-system communication.
    Phase 1.1: Bidirectional event flow.
    """
    try:
        from app.core.integration import initialize_bus_subscribers as init_subscribers
        count = init_subscribers()
        logger.info(f"🔗 Initialized {count} bus subscribers")
    except Exception as e:
        logger.warning(f"Bus subscriber initialization failed: {e}")


def main() -> None:
    try:
        logger.info("Starting Astra...")
        token = load_environment()
        
        # Run startup coherence check (Phase 1.3)
        run_startup_coherence_check()
        
        # Initialize bus subscribers for cross-system communication (Phase 1.1)
        initialize_bus_subscribers()
        
        # Restore identity on startup (Phase 8)
        startup_identity_restoration()
        
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
