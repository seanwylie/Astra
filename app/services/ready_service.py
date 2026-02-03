# ready_service.py

"""
✅ Ready Service
----------------
Handles Astra’s `on_ready()` Discord event.

This includes:
- Sending a mood-aware welcome message
- Displaying categorized command help using the same formatting as `!commands`
(Schedule loop is started by start_schedule() in main.on_ready.)

Author: Sean Wylie
Updated: 2025-04-15
"""

# --- Imports ---
import aiohttp
from app.core.messaging.message_bus import (
    describe_emotional_state,
    get_dominant_emotion
)
from app.core.emotions.emotion_engine import load_emotion_state
from app.commands.help_commands import _get_formatted_command_list  # ✅ Using correct internal method


# --- Public Interface ---

async def handle_on_ready(bot, channel_id: int):
    """
    Executes Astra’s startup routine when the Discord bot is ready.

    Args:
        bot (commands.Bot): The running bot instance.
        channel_id (int): Discord channel ID for startup message.

    Workflow:
    - Sends Astra's welcome message and categorized help list
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

    # Step 3: Generate full command help text
    help_text = _get_formatted_command_list(bot)

    # Step 4: Send welcome and help messages
    try:
        await channel.send("🟢 **Astra is online and ready to engage!**")
        if mood_line:
            await channel.send(mood_line.strip())

        for i in range(0, len(help_text), 1900):
            await channel.send(help_text[i:i + 1900])

    except aiohttp.ClientOSError as e:
        print(f"⚠️ Discord send failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error while sending to Discord: {e}")

    # Step 5: Start Astra’s async schedule loop
    # Schedule loop is started by start_schedule() in main.on_ready (single loop only).
