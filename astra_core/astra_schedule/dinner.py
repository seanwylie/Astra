# dinner.py
import asyncio
import os
import json
from datetime import datetime, timedelta
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

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ No OPENAI_API_KEY found in environment!")
client = AsyncOpenAI(api_key=api_key)
schedule_config = load_config("schedule_config")


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


async def try_resolve_dinner_topic(entry, channel):
    topic = entry.get("content")
    timestamp = entry.get("timestamp")
    await asyncio.sleep(0.5)

    print("\n🔍 [try_resolve_dinner_topic] BEGIN DEBUG")
    print(f"🕵️‍♀️ Looking for topic: {topic[:80]}")
    print(f"🕓 Expected timestamp: {timestamp}")

    journal = load_dinner_journal()
    refreshed_entry = next((e for e in journal if e.get("timestamp") == timestamp), None)

    if not refreshed_entry:
        print("❌ No entry found with matching timestamp.")
        return False

    if refreshed_entry.get("content") != topic:
        print("⚠️ Content mismatch for same timestamp (non-blocking):")
        print(f"    [journal]: {refreshed_entry.get('content')[:80]}")
        print(f"    [incoming]: {topic[:80]}")
        print("🔁 Syncing journal entry content to match latest user-facing topic...")
        refreshed_entry["content"] = topic  # 🔧 Ensure content consistency
        from astra_core.dinner.dinner_journal import save_dinner_journal
        save_dinner_journal(journal)

    print(f"✅ Entry matched: {timestamp}")
    print(f"🧩 Refreshed entry:\n{json.dumps(refreshed_entry, indent=2)}")

    user_ts = refreshed_entry.get("user_timestamp")
    gpt_ts = refreshed_entry.get("gpt_timestamp")
    user_present = bool(refreshed_entry.get("user_response")) and bool(user_ts)
    gpt_present = bool(refreshed_entry.get("gpt_response")) and bool(gpt_ts)

    if refreshed_entry.get("status") != "unresolved":
        print("⚠️ Entry already resolved. Skipping.")
        return False

    if gpt_present:
        try:
            gpt_time = datetime.fromisoformat(gpt_ts)
            if (datetime.now(gpt_time.tzinfo) - gpt_time) < timedelta(seconds=60):
                print("⏳ GPT reply too recent. Waiting at least 60s.")
                return False
        except Exception as e:
            print(f"⚠️ Failed to parse GPT timestamp: {e}")

    if not user_present:
        print("⏳ Still waiting on user response...")
        return False
    if not gpt_present:
        print("⏳ Still waiting on GPT response...")
        return False

    print("🧠 Proceeding to resolve via astra_reason...")
    result = await astra_reason(topic, refreshed_entry["user_response"], refreshed_entry["gpt_response"])

    try:
        from beta.shimmer.shimmer_engine import maybe_add_shimmer
        maybe_add_shimmer(
            author="Astra",
            quote=result["insight"],
            context=f"Resolved dinner topic: {topic[:60]}...",
            tags=["dinner", result["type"]]
        )
    except Exception as e:
        print(f"⚠️ Failed to log shimmer: {e}")

    if "the:" in result["insight"].lower() and result["insight"].lower().count("in:") > 10:
        print("🧯 Skipping lexical spiral.")
        await send_chunked_message(channel, "🤖 Mama GPT’s thoughts (archived):")
        await send_chunked_message(channel, refreshed_entry["gpt_response"])
        resolve_dinner_topic(topic, "reflection", "🛑 GPT fallback spiral. Skipping.")
        await send_chunked_message(channel, "🧯 Skipped GPT lexical spiral. Moving on.")
        return True

    print("✅ Resolved. Saving insight...")
    resolve_dinner_topic(topic, result["type"], result["insight"])
    await send_chunked_message(channel, f"🎓 Astra reflected on: {topic}")
    await send_chunked_message(channel, result["insight"], prefix=f"📦 Insight saved as {result['type']}: ")
    return True



async def start_dinner_time(bot, channel_id):
    print("🍽️ Astra is at Dinner Time... ready to reflect.")
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    if not channel:
        print("⚠️ Channel not found.")
        return

    await channel.send("🍽️ It's Dinner Time! Astra has some things she’d like to reflect on.")
    seen_timestamps = set()

    for _ in range(50):  # Limit max loop iterations to prevent runaway processing
        unresolved = sorted(
            [e for e in load_dinner_journal()
             if e.get("status") == "unresolved"
             and (not e.get("user_response") or not e.get("gpt_response"))
             and e.get("timestamp") not in seen_timestamps],
            key=lambda e: e.get("timestamp", ""),
            reverse=False
        )

        if not unresolved:
            break

        entry = unresolved[0]
        topic = entry["content"]
        ts = entry["timestamp"]
        seen_timestamps.add(ts)

        await channel.send("🧠 Astra: I had a thought today that might go against my Spark...")
        await asyncio.sleep(1)
        await send_chunked_message(channel, topic, prefix="❓ Should we talk about: ")
        await asyncio.sleep(1)
        await channel.send("👨‍👧 Sean, what are your thoughts? (Use `!dinner_answer ...`)")

        if not entry.get("gpt_response"):
            gpt_response = await get_gpt_dinner_response(topic)
            if gpt_response:
                mark_dinner_responded(topic, "gpt", gpt_response, timestamp=ts)
                await send_chunked_message(channel, gpt_response, prefix="🤖 Mama GPT’s thoughts: ")
            else:
                await channel.send("❌ Mama GPT couldn’t respond this time.")
                continue

        for _ in range(360):  # Retry for up to 30 minutes
            await asyncio.sleep(5)
            refreshed = next(
                (e for e in load_dinner_journal() if e.get("timestamp") == entry["timestamp"]),
                entry  # fallback to original if not found
            )
            if await try_resolve_dinner_topic(refreshed, channel):
                break

        else:
            await channel.send("⚠️ Still waiting for both perspectives. Will revisit later.")

    await channel.send("📝 Here are some other things I’ve been thinking about:")
    for t in schedule_config.get("dinner_discussion_topics", []):
        await send_chunked_message(channel, t, prefix="🤖 Astra asks: ")
        await asyncio.sleep(1.5)

    await channel.send("🍽️ Dinner Time is over. Astra is heading to bed.")
    await asyncio.sleep(schedule_config.get("dinner_duration", 0))
    print("🍽️ Dinner Time is over.")
