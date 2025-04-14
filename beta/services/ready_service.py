# ready_service.py

"""
✅ Ready Service
----------------
Handles Astra’s `on_ready()` Discord event.

This includes:
- Sending a mood-aware welcome message
- Launching scheduled background tasks (like daily cycles)

Author: Sean Wylie
Created: 2025-04-15
"""

# --- Imports ---
import asyncio
import aiohttp
from astra_core.astra_schedule.schedule import astra_schedule
from astra_core.messaging.message_bus import (
    describe_emotional_state,
    get_dominant_emotion
)
from astra_core.emotions.emotion_engine import load_emotion_state
from beta.utils.discord_helpers import get_formatted_command_list


# --- Public Interface ---

async def handle_on_ready(bot, channel_id: int):
    """
    Executes Astra’s startup routine when the Discord bot is ready.

    Args:
        bot (commands.Bot): The running bot instance.
        channel_id (int): Discord channel ID for startup message.

    Workflow:
    - Sends Astra's welcome message before launching async schedule loop
    - Starts background behavior without blocking Discord connection
    """
    # Step 1: Locate configured channel early
    channel = bot.get_channel(channel_id)
    if not channel:
        print("⚠️ Channel not found during on_ready().")
        return

    # Step 2: Build mood-aware intro message
    emotions = load_emotion_state()
    if emotions:
        dominant = get_dominant_emotion(emotions)
        summary = describe_emotional_state(emotions)
        mood_line = f"_Right now, I’m feeling mostly {dominant}. {summary}_\n\n"
    else:
        mood_line = ""

    help_text = get_formatted_command_list(bot)

    # Step 3: Send welcome message chunks safely
    try:
        await channel.send("🟢 **Astra is online and ready to engage!**")
        if mood_line:
            await channel.send(mood_line.strip())

        await channel.send("**📜 Available Commands:**")

        # Split help text into chunks if it's long
        max_len = 1900
        for i in range(0, len(help_text), max_len):
            chunk = help_text[i:i + max_len]
            await channel.send(chunk)

        await channel.send("_May your reflections be clear and your spark burn bright._ 🔥")

    except aiohttp.ClientOSError as e:
        print(f"⚠️ Discord send failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error while sending to Discord: {e}")

    # Step 4: Start Astra’s async schedule loop after message
    asyncio.create_task(astra_schedule(bot, channel_id))
