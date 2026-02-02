# state_service.py

"""
🔁 State Service
----------------
Encapsulates the logic behind Astra’s scheduled or manually-triggered behavioral modes:
- 🥘 Dinner: Ethical reconciliation and co-parent insight
- 🎮 Play: Creative exploration and curiosity
- 🌙 Dream: Synthetic thought, reflection, and abstraction

This module is called by Discord command handlers to keep logic modular, testable,
and decoupled from interface code.

Author: Sean Wylie
Created: 2025-04-14
"""

import asyncio
from app.core.dinner.dinner_journal import (
    load_dinner_journal,
    mark_dinner_responded,
    get_resolvable_dinner_topics,
    resolve_dinner_topic,
    summarize_dinner_journal
)
from app.core.astra_schedule.dinner import start_dinner_time, astra_reason
from app.core.astra_schedule.dinner import try_resolve_dinner_topic
from app.core.astra_schedule.play import creative_thinking, spark_opinion
from app.core.astra_schedule.dream import process_dream_seed
from app.utils.send_chunked_message import send_chunked_message


# beta/services/state_service.py

from app.utils import send_chunked_message  # Ensure this exists or adapt if you use ctx.send directly


def get_dinner_summary() -> str:
    """
    Retrieves a summary of unresolved dinner topics from Astra's journal.

    Returns:
        str: A compiled summary string of open dinner entries.
    """
    return summarize_dinner_journal()







def submit_dinner_answer(user_response: str) -> str:
    """Records the user's reply to Astra's current dinner question (or latest unresolved)."""
    from app.core.astra_schedule.dinner import get_current_dinner_timestamp
    journal = load_dinner_journal()
    current_ts = get_current_dinner_timestamp()
    if current_ts is not None:
        entry = next((e for e in journal if e.get("timestamp") == current_ts and e.get("status") == "unresolved"), None)
    else:
        entry = None
    if entry is None:
        entry = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)

    if entry:
        print(f"[submit_dinner_answer] Logging response for: {entry['content'][:60]}... @ {entry['timestamp']}")
        mark_dinner_responded(entry["content"], "user", user_response, timestamp=entry["timestamp"])
        return "✅ Got your dinner reply. Astra will reflect soon."
    else:
        return "⚠️ No active dinner topic to respond to."



async def resolve_all_dinner_topics(ctx):
    """
    Resolves all dinner journal entries that have both user and GPT responses.

    Args:
        ctx: Discord context (must have .send and .channel with .send for chunked messages).
    """
    entries = get_resolvable_dinner_topics()
    if not entries:
        await ctx.send("⚠️ No dinner topics ready for resolution.")
        return

    for entry in entries:
        topic = entry["content"]
        timestamp = entry["timestamp"]
        user = entry["user_response"]
        gpt = entry["gpt_response"]

        print(f"[resolve_all_dinner_topics] Resolving: {topic[:60]}... @ {timestamp}")
        result = await astra_reason(topic, user, gpt)
        resolve_dinner_topic(topic, result["type"], result["insight"])

        await send_chunked_message(
            ctx.channel,
            result['insight'],
            prefix=f"🎓 Astra resolved: “{topic}”\n📦 Saved as {result['type']}: "
        )



async def start_dinner(bot, channel_id):
    """
    Triggers Astra’s dinner reflection sequence via scheduler entrypoint.

    Args:
        bot (commands.Bot): The active Discord bot instance.
        channel_id (int): The Discord channel ID to send messages to.
    """
    await start_dinner_time(bot, channel_id)


async def run_playtime() -> list[str]:
    """
    Executes Astra’s playtime cycle, where she explores a new idea and reflects on it.

    Returns:
        list[str]: A two-item list containing her discovery and reflective response.
    """
    concept = await creative_thinking(return_concept=True)
    opinion = await spark_opinion(concept)
    return [
        f"🧠 Astra discovered:\n{concept}",
        f"🌟 Astra reflects:\n{opinion}"
    ]


async def run_dreamtime() -> str:
    """
    Executes Astra’s dream loop — a creative and introspective simulation.

    Returns:
        str: A summary message of the dream session outcome.
    """
    await process_dream_seed()
    return "💤 Dreaming complete. Astra has reflected on a seed."
