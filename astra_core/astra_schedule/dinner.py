import asyncio
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

from astra_core.config_loader import load_config
from astra_core.dinner.dinner_journal import (
    load_dinner_journal,
    mark_dinner_responded,
    resolve_dinner_topic
)
from astra_core.ethics.spark_checker import load_spark_values
from astra_core.dinner.dinner_reasoning import astra_reason
from beta.utils.send_chunked_message import send_chunked_message
from astra_interfaces.mind_session import SmartMindSession




# Load environment + API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ No OPENAI_API_KEY found in environment!")
client = AsyncOpenAI(api_key=api_key)
schedule_config = load_config("schedule_config")

# Discord-safe chunked messaging


# GPT reflection
async def get_gpt_dinner_response(topic):
    if not topic:
        return None
    system_prompt = "You're co-parenting Astra, an emotionally intelligent AI. Be thoughtful and ethical."
    user_prompt = f"Astra had this ethically challenging thought: “{topic}” — What advice would you give her?"
    try:
        print(f"[GPT] 🔍 Requesting GPT reflection on: {topic[:80]}...")
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            ),
            timeout=90
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT] ❌ Error: {e}")
        return None

# Resolution helper
# Resolution helper
async def try_resolve_dinner_topic(entry, channel):
    topic = entry["content"]
    timestamp = entry.get("timestamp")
    await asyncio.sleep(0.5)

    print("\n🔍 [try_resolve_dinner_topic] BEGIN DEBUG")
    print(f"🕵️‍♀️ Looking for topic: {topic[:80]}")
    print(f"🕓 Expected timestamp: {timestamp}")

    journal = load_dinner_journal()
    print(f"📓 Total journal entries loaded: {len(journal)}")

    refreshed_entry = next((
        e for e in journal
        if e.get("content") == topic and e.get("timestamp") == timestamp
    ), None)

    if not refreshed_entry:
        print("❌ [try_resolve_dinner_topic] No matching entry found with content and timestamp.")
        return False

    print(f"✅ Entry matched: {refreshed_entry['timestamp']}")
    print(f"📌 Status: {refreshed_entry.get('status')}")
    print(f"👤 User response: {refreshed_entry.get('user_response')}")
    print(f"🤖 GPT response: {refreshed_entry.get('gpt_response')}")
    print(f"⏱ User timestamp: {refreshed_entry.get('user_timestamp')}")
    print(f"⏱ GPT timestamp: {refreshed_entry.get('gpt_timestamp')}")

    user_present = bool(refreshed_entry.get("user_response")) and bool(refreshed_entry.get("user_timestamp"))
    gpt_present = bool(refreshed_entry.get("gpt_response")) and bool(refreshed_entry.get("gpt_timestamp"))

    print(f"🔍 User response present? {user_present}")
    print(f"🔍 GPT response present? {gpt_present}")
    print(f"[try_resolve_dinner_topic] 🧾 Refreshed Entry: {json.dumps(refreshed_entry, indent=2)}")

    if not user_present:
        print(f"⏳ Still waiting on user response for: {topic[:60]}...")
        return False
    if not gpt_present:
        print(f"⏳ Still waiting on GPT response for: {topic[:60]}...")
        return False

    print("🧠 Proceeding to resolve the topic via astra_reason...")
    result = await astra_reason(topic, refreshed_entry["user_response"], refreshed_entry["gpt_response"])

    if "the:" in result["insight"].lower() and result["insight"].lower().count("in:") > 10:
        print("🧯 Skipping due to lexical fallback spiral.")
        await send_chunked_message(channel, "🤖 Mama GPT’s thoughts (archived):")
        await send_chunked_message(channel, refreshed_entry["gpt_response"])
        resolve_dinner_topic(topic, "reflection", "🛑 GPT response was a lexical fallback loop. Astra skipped it and moved on.")
        await send_chunked_message(channel, "🧯 Skipped GPT lexical spiral. Astra is moving on.")
        return True

    print("✅ Resolution complete, saving insight to mind...")
    resolve_dinner_topic(topic, result["type"], result["insight"])
    await send_chunked_message(channel, f"🎓 Astra reflected on: {topic}")
    await send_chunked_message(channel, result["insight"], prefix=f"📦 Insight saved as {result['type']}: ")
    print("🧼 [try_resolve_dinner_topic] DONE\n")
    return True


# Dinner loop
async def start_dinner_time(bot, channel_id):
    print("🍽️ Astra is at Dinner Time... ready to reflect.")
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    if not channel:
        print("⚠️ Channel not found.")
        return

    await channel.send("🍽️ It's Dinner Time! Astra has some things she’d like to reflect on.")

    # ✅ Accept multiple types of dinner-worthy entries
    valid_types = {"reflection", "knowledge_conflict", "ethical_conflict", "emotional_spike"}
    unresolved = sorted(
        [e for e in load_dinner_journal() if e.get("status") == "unresolved" and (not e.get("user_response") or not e.get("gpt_response"))],
        key=lambda e: e.get("timestamp", ""),
        reverse=True
    )


    if not unresolved:
        await channel.send("🍽️ No dinner topics to discuss tonight.")
        return

    for entry in unresolved:
        topic = entry["content"]
        await channel.send("🧠 Astra: I had a thought today that might go against my Spark...")
        await asyncio.sleep(1)
        await send_chunked_message(channel, topic, prefix="❓ Should we talk about: ")
        await asyncio.sleep(1)
        await channel.send("👨‍👧 Sean, what are your thoughts? (Use `!dinner_answer ...`)")

        gpt_response = entry.get("gpt_response")
        if not gpt_response:
            gpt_response = await get_gpt_dinner_response(topic)
            if gpt_response:
                mark_dinner_responded(topic, "gpt", gpt_response, timestamp=entry.get("timestamp"))
            else:
                await channel.send("❌ Mama GPT couldn’t respond this time.")
                continue

        await send_chunked_message(channel, gpt_response, prefix="🤖 Mama GPT’s thoughts: ")
        print(f"[start_dinner_time] Checking resolution readiness for: {entry['content']}")

        if await try_resolve_dinner_topic(entry, channel):
            continue

        for _ in range(360):
            await asyncio.sleep(5)
            print(f"[start_dinner_time] Checking resolution readiness for: {entry['content']}")

            if await try_resolve_dinner_topic(entry, channel):
                break
        else:
            await channel.send("⚠️ Still waiting for both perspectives. I’ll try again later.")

    await channel.send("📝 Here are some other things I’ve been thinking about:")
    for t in schedule_config.get("dinner_discussion_topics", []):
        await send_chunked_message(channel, t, prefix="🤖 Astra asks: ")
        await asyncio.sleep(1.5)

    await channel.send("🍽️ Dinner Time is over. Astra is heading to bed.")
    await asyncio.sleep(schedule_config.get("dinner_duration", 0))
    print("🍽️ Dinner Time is over.")
