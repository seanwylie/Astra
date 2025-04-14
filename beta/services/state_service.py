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
from astra_core.dinner.dinner_journal import (
    load_dinner_journal,
    mark_dinner_responded,
    get_resolvable_dinner_topics,
    resolve_dinner_topic,
    summarize_dinner_journal
)
from astra_core.astra_schedule.dinner import start_dinner_time, astra_reason
from astra_core.astra_schedule.play import creative_thinking, spark_opinion
from astra_core.astra_schedule.dream import process_dream_seed


def get_dinner_summary() -> str:
    """
    Retrieves a summary of unresolved dinner topics from Astra's journal.

    Returns:
        str: A compiled summary string of open dinner entries.
    """
    return summarize_dinner_journal()


def submit_dinner_answer(user_response: str) -> str:
    """
    Records the user's reply to Astra's most recent unresolved dinner question.

    Args:
        user_response (str): The message content from the user.

    Returns:
        str: A success or failure response message.
    """
    journal = load_dinner_journal()
    latest = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)

    if latest:
        mark_dinner_responded(latest["content"], "user", user_response)
        return "✅ Got your dinner reply. Astra will reflect soon."
    else:
        return "⚠️ No active dinner topic to respond to."


async def resolve_all_dinner_topics(send_func):
    """
    Resolves all dinner journal entries that have both user and GPT responses.

    Args:
        send_func (Callable): An async callback function (e.g., ctx.send) to send output.
    """
    entries = get_resolvable_dinner_topics()
    if not entries:
        await send_func("⚠️ No dinner topics ready for resolution.")
        return

    for entry in entries:
        topic = entry["content"]
        user = entry["user_response"]
        gpt = entry["gpt_response"]
        result = await astra_reason(topic, user, gpt)
        resolve_dinner_topic(topic, result["type"], result["insight"])
        await send_func(f"🎓 Astra resolved: “{topic}”\n📦 Saved as {result['type']}: {result['insight']}")


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
