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

from app.config.loader import config_manager, debug_log, get_s3_bucket
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
    }
    from app.config.loader import s3_sync_enabled
    if s3_sync_enabled():
        required["AWS_ACCESS_KEY_ID"] = "AWS access key"
        required["AWS_SECRET_ACCESS_KEY"] = "AWS secret key"
        if not get_s3_bucket():
            logger.error("s3_sync_enabled is true but no S3 bucket is configured")
            sys.exit(1)
    missing = [var for var, _ in required.items() if not os.getenv(var)]
    if missing:
        logger.error("Missing required env: %s", missing)
        sys.exit(1)
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
    # Enable all necessary intents for message handling
    intents = discord.Intents.default()
    intents.message_content = True  # Required to read message content
    intents.messages = True  # Required to receive message events
    intents.guilds = True  # Required for guild/channel access
    intents.members = True  # May be needed for some features
    
    logger.info("Discord intents configured: message_content=%s, messages=%s, guilds=%s", 
                intents.message_content, intents.messages, intents.guilds)
    
    bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
    return bot, int(channel_id), values_config


def setup_event_handlers(bot, channel_id, values_config):
    """Attach Discord event handlers."""
    
    # CRITICAL: When overriding on_message in commands.Bot, we MUST call process_commands
    # But first, let's verify the event is being registered
    
    @bot.event
    async def on_message(message):
        # Log ALL messages received, even before ready check - this should ALWAYS fire
        logger.info("=" * 80)
        logger.info("📨📨📨 on_message EVENT TRIGGERED 📨📨📨")
        logger.info("Author: %s (ID: %s)", message.author, message.author.id if message.author else "None")
        logger.info("Content: %s", message.content[:200] if message.content else "(no content)")
        logger.info("Channel: %s (ID: %s)", message.channel, message.channel.id if message.channel else "None")
        logger.info("Guild: %s (ID: %s)", message.guild.name if message.guild else "DM", message.guild.id if message.guild else "None")
        logger.info("Bot user: %s (ID: %s)", bot.user, bot.user.id if bot.user else "None")
        logger.info("Bot ready: %s", bot.is_ready())
        logger.info("=" * 80)
        
        try:
            # CRITICAL: Process commands first - this is required for commands.Bot
            await bot.process_commands(message)
            
            # Ensure bot is ready before processing messages
            if not bot.is_ready():
                logger.warning("Bot not ready yet, ignoring message from %s", message.author)
                return
            
            # Skip bot's own messages
            if message.author == bot.user:
                logger.debug("Skipping message from bot itself")
                return
            
            logger.info("📨 Processing message from %s: %s", message.author, message.content[:100] if message.content else "(empty)")
            await handle_message(
                bot, message, values_config, values_config.get("values", {})
            )
        except Exception as e:
            logger.exception("Error handling message: %s", e)

    @bot.event
    async def on_ready():
        logger.info("=" * 80)
        logger.info("✅ Bot is ready! Logged in as %s (ID: %s)", bot.user, bot.user.id if bot.user else "None")
        logger.info("Bot username: %s#%s", bot.user.name if bot.user else "None", bot.user.discriminator if bot.user else "None")
        logger.info("✅ Bot is in %s guilds", len(bot.guilds))
        
        if len(bot.guilds) == 0:
            logger.error("=" * 80)
            logger.error("❌ CRITICAL: BOT IS NOT IN ANY SERVERS!")
            logger.error("Astra cannot receive messages if she's not in your Discord server.")
            logger.error("")
            logger.error("To fix this:")
            logger.error("1. Go to Discord Developer Portal: https://discord.com/developers/applications")
            logger.error("2. Select your bot application")
            logger.error("3. Go to OAuth2 → URL Generator")
            logger.error("4. Select 'bot' scope and these permissions:")
            logger.error("   - Read Messages/View Channels")
            logger.error("   - Send Messages")
            logger.error("   - Read Message History")
            logger.error("   - Use External Emojis")
            logger.error("   - Add Reactions")
            logger.error("5. Copy the generated URL and open it in a browser")
            logger.error("6. Select your server and authorize")
            logger.error("=" * 80)
        else:
            for guild in bot.guilds:
                logger.info("  - Guild: %s (ID: %s)", guild.name, guild.id)
                # Check if bot member exists
                try:
                    member = guild.get_member(bot.user.id) if bot.user else None
                    if member:
                        logger.info("    Bot is visible in member list: ✅")
                        logger.info("    Bot nickname: %s", member.display_name)
                    else:
                        logger.warning("    ⚠️ Bot member object not found - may not be visible")
                except Exception as e:
                    logger.warning("    ⚠️ Error checking member: %s", e)
        logger.info("=" * 80)
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
    
    @bot.event
    async def on_disconnect():
        """Handle Discord gateway disconnections with reconnection logic."""
        logger.warning("⚠️ Discord gateway disconnected - attempting reconnection...")
        # Discord.py handles reconnection automatically, but we log it for monitoring
    
    @bot.event
    async def on_resume():
        """Handle Discord gateway reconnection after disconnect."""
        logger.info("✅ Discord gateway reconnected successfully")
    
    @bot.event
    async def on_connect():
        """Handle Discord gateway initial connection."""
        logger.info("=" * 80)
        logger.info("🔌 Discord gateway connected - Bot authenticated successfully")
        logger.info("=" * 80)
    
    @bot.event
    async def on_guild_join(guild):
        """Handle bot joining a new guild."""
        logger.info("=" * 80)
        logger.info("🎉 Astra joined guild: %s (ID: %s)", guild.name, guild.id)
        logger.info("=" * 80)
    
    @bot.event
    async def on_socket_raw_receive(msg):
        """Monitor gateway heartbeat for unresponsiveness detection."""
        # This is called for every gateway event - we can use it to detect unresponsiveness
        # Discord.py handles heartbeat internally, but we log if there are issues
        # Log message events to verify we're receiving them
        if isinstance(msg, dict) and msg.get('t') == 'MESSAGE_CREATE':
            logger.debug("🔍 Raw MESSAGE_CREATE event received from gateway")
    
    @bot.event
    async def on_raw_message_create(payload):
        """Fallback handler for raw message events - helps diagnose if on_message isn't firing."""
        logger.info("=" * 80)
        logger.info("🔍🔍🔍 on_raw_message_create TRIGGERED 🔍🔍🔍")
        logger.info("This means Discord IS sending message events to the bot!")
        logger.info("Message ID: %s", payload.message_id if hasattr(payload, 'message_id') else 'unknown')
        logger.info("Author ID: %s", payload.user_id if hasattr(payload, 'user_id') else payload.get('author', {}).get('id', 'unknown'))
        logger.info("Channel ID: %s", payload.channel_id if hasattr(payload, 'channel_id') else 'unknown')
        logger.info("=" * 80)


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
        logger.info("Setting up event handlers...")
        setup_event_handlers(bot, channel_id, values_config)
        
        # Verify event handlers are registered BEFORE starting the bot
        logger.info("=" * 80)
        logger.info("EVENT HANDLER REGISTRATION CHECK (BEFORE bot.run):")
        if hasattr(bot, '_listeners'):
            listeners = bot._listeners
            logger.info("Registered event listeners:")
            for event_name, handlers in listeners.items():
                logger.info("  - %s: %d handler(s)", event_name, len(handlers))
            if 'on_message' in listeners:
                logger.info("✅ on_message handler IS registered with %d handler(s)", len(listeners['on_message']))
                # Verify it's our handler
                for i, handler in enumerate(listeners['on_message']):
                    logger.info("    Handler %d: %s", i, handler)
            else:
                logger.error("❌ on_message handler NOT found in listeners!")
                logger.error("This is a CRITICAL issue - messages will not be processed!")
        else:
            logger.warning("⚠️ Bot._listeners not accessible")
        logger.info("=" * 80)
        
        # Also verify bot is using correct intents
        logger.info("Bot intents verification:")
        logger.info("  message_content: %s", bot.intents.message_content)
        logger.info("  messages: %s", bot.intents.messages)
        logger.info("  guilds: %s", bot.intents.guilds)
        logger.info("=" * 80)
        MoodManager()
        MessageGenerator()
        debug_log("Loading Astra core", "general")
        session.load()
        
        # MEMORY LEAK FIX: Start periodic cache cleanup
        import threading
        from app.utils.cache import periodic_cache_cleanup
        
        def cache_cleanup_loop():
            """Periodic cache cleanup to prevent memory leaks."""
            import time
            while True:
                time.sleep(300)  # Every 5 minutes
                try:
                    periodic_cache_cleanup()
                except Exception as e:
                    logger.warning(f"Cache cleanup failed: {e}")
        
        cleanup_thread = threading.Thread(target=cache_cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Cache cleanup thread started")
        
        logger.info("Astra initialized successfully. Starting bot...")
        logger.info("Bot will connect to Discord. Watch for 'on_ready' and 'on_connect' events.")
        logger.info("Bot token length: %d characters", len(token))
        logger.info("Bot token starts with: %s...", token[:10] if len(token) > 10 else token)
        
        # Final verification before starting
        logger.info("=" * 80)
        logger.info("FINAL VERIFICATION BEFORE STARTING BOT:")
        logger.info("Bot class: %s", type(bot).__name__)
        logger.info("Bot intents.message_content: %s", bot.intents.message_content)
        logger.info("Bot intents.messages: %s", bot.intents.messages)
        logger.info("Has on_message listener: %s", 'on_message' in (bot._listeners if hasattr(bot, '_listeners') else {}))
        logger.info("=" * 80)
        
        try:
            bot.run(token)
        except discord.LoginFailure as e:
            logger.error("=" * 80)
            logger.error("❌ DISCORD LOGIN FAILED!")
            logger.error("Error: %s", e)
            logger.error("Check your TOKEN environment variable")
            logger.error("=" * 80)
            raise
        except Exception as e:
            logger.exception("Fatal error starting bot: %s", e)
            raise
    except KeyboardInterrupt:
        logger.info("Shutting down Astra...")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
