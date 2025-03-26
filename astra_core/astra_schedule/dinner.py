import time
from astra_core.config_loader import load_config
from astra_helpers.sms_helper import send_sms
from astra_core.discord_astra import bot, CHANNEL_ID
import asyncio
import threading

schedule_config = load_config("schedule_config")

def start_dinner_time():
    """Dinner Time: Astra checks in with us, shares her thoughts, and receives new guidance."""
    print("🍽️ Astra is at Dinner Time... ready to discuss her day.")

    # ✅ Send SMS Notification
    send_sms("dinner_time")

    # ✅ Launch Discord discussion in a new thread
    threading.Thread(target=lambda: asyncio.run(discord_dinner_conversation())).start()

    # ✅ Simulate local delay for dinner duration
    time.sleep(schedule_config.get("dinner_duration", 0))
    print("🍽️ Dinner Time is over. Astra returns to school.")

async def discord_dinner_conversation():
    """Sends dinner prompts to the Discord channel."""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🍽️ It's Dinner Time! Astra wants to share her thoughts and ask some questions.")
        discussion_topics = schedule_config.get("dinner_discussion_topics", [])
        for topic in discussion_topics:
            await channel.send(f"🤖 Astra asks: {topic}")
            await asyncio.sleep(2)  # Give users breathing room between questions
        await channel.send("🍽️ Dinner Time is over. Astra returns to school.")
