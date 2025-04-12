import time
import asyncio
from astra_core.config_loader import load_config
from astra_core.astra_helpers.sms_helper import send_sms

schedule_config = load_config("schedule_config")

async def start_dinner_time(bot, channel_id):
    """Dinner Time: Astra checks in with us, shares her thoughts, and receives new guidance."""
    print("🍽️ Astra is at Dinner Time... ready to discuss her day.")

    # ✅ Send SMS Notification
    send_sms("dinner_time")

    # ✅ Wait until the bot is fully ready before sending messages
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)

    if not channel:
        print("⚠️ Discord channel not found.")
        return

    # ✅ Send dinner discussion prompts
    await channel.send("🍽️ It's Dinner Time! Astra wants to share her thoughts and ask some questions.")
    discussion_topics = schedule_config.get("dinner_discussion_topics", [])
    for topic in discussion_topics:
        await channel.send(f"🤖 Astra asks: {topic}")
        await asyncio.sleep(2)  # Breathing room between questions
    await channel.send("🍽️ Dinner Time is over. Astra returns to school.")

    # ✅ Simulate dinner duration
    await asyncio.sleep(schedule_config.get("dinner_duration", 0))
    print("🍽️ Dinner Time is over. Astra returns to school.")
