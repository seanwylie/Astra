"""
🚀 Astra Entry Point (main.py)
------------------------------
Modern, robust launch script for Astra's Discord interface.
Features improved error handling, configuration management,
and modular service architecture.

Author: Sean Wylie
Updated: 2025-04-14
"""

import os
import sys
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

# --- Beta Configuration System ---
from beta.config.beta_config import config_manager
from astra_core.config_loader import debug_log

# --- Core Services ---
from astra_interfaces.mind_session import session
from astra_core.mood.mood_manager import MoodManager
from astra_core.message_generator import MessageGenerator

# --- Bot Subsystems ---
from beta.commands.register_all_commands import register_all_commands
from beta.events.message_event import handle_message
from beta.services.ready_service import handle_on_ready

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('astra.main')

def load_environment():
    """Load and validate environment variables."""
    # Load from both local .env and ~/.env
    load_dotenv(find_dotenv())
    load_dotenv(os.path.expanduser("~/.env"))
    
    # Check required variables
    required_vars = {
        'TOKEN': 'Discord bot token',
        'OPENAI_API_KEY': 'OpenAI API key',
        'AWS_ACCESS_KEY_ID': 'AWS access key',
        'AWS_SECRET_ACCESS_KEY': 'AWS secret key'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            logger.error(f"❌ {var} ({description}) not found in environment variables")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Set S3 bucket name if not already set
    if not os.getenv("S3_BUCKET_NAME"):
        os.environ["S3_BUCKET_NAME"] = "swylie-astra"
        logger.info("🪣 Set S3_BUCKET_NAME to default: swylie-astra")
    
    token = os.getenv("TOKEN")
    logger.info("✅ All required environment variables loaded successfully")
    return token.strip()

def initialize_bot():
    """Initialize Discord bot with proper configuration."""
    try:
        # Load configurations
        discord_config = config_manager.get_discord_config()
        values_config = config_manager.get_values_config()
        
        if not discord_config or not values_config:
            logger.error("❌ Failed to load required configuration files")
            sys.exit(1)
        
        # Extract values
        command_prefix = values_config.get("values", {}).get("command_prefix", "!")
        channel_id = discord_config.get("discord_channel")
        
        if not channel_id:
            logger.error("❌ discord_channel not configured")
            sys.exit(1)
            
        # Initialize bot
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents,
            help_command=None
        )
        
        return bot, int(channel_id), values_config
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        sys.exit(1)

def setup_event_handlers(bot, channel_id, values_config):
    """Setup Discord event handlers."""
    
    @bot.event
    async def on_message(message):
        """Handle incoming Discord messages."""
        try:
            await handle_message(bot, message, values_config, values_config.get("values", {}))
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            # Don't crash the bot on message handling errors
    
    @bot.event
    async def on_ready():
        """Handle bot ready event."""
        try:
            await handle_on_ready(bot, channel_id)
            
            # Start the automated schedule
            from beta.services.schedule_service import start_schedule
            await start_schedule(bot, channel_id)
            logger.info("⏰ Automated schedule started")
            
        except Exception as e:
            logger.error(f"❌ Error in on_ready: {e}")
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        """Handle Discord errors gracefully."""
        logger.error(f"❌ Discord error in {event}: {args}")

def main():
    """Main entry point."""
    try:
        logger.info("🚀 Starting Astra Beta...")
        
        # Load environment
        token = load_environment()
        
        # Initialize bot
        bot, channel_id, values_config = initialize_bot()
        
        # Register commands
        logger.info("🔧 Registering commands...")
        register_all_commands(bot)
        
        # Setup event handlers
        setup_event_handlers(bot, channel_id, values_config)
        
        # Initialize core services
        logger.info("🧠 Initializing core services...")
        mood_manager = MoodManager()
        message_generator = MessageGenerator()
        
        # Load mind data
        debug_log("Loading Astra core")
        mind_data = session.load()
        
        logger.info("✅ Astra Beta initialized successfully")
        
        # Run bot
        bot.run(token)
        
    except KeyboardInterrupt:
        logger.info("👋 Astra Beta shutting down gracefully...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
