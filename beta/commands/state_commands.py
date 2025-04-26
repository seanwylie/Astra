# state_commands.py

"""
⏳ State Commands
-----------------
Commands that manage Astra's behavioral states:
- 🥘 Dinner (ethical reflection)
- 🎮 Playtime (creative exploration)
- 🌙 Dreamtime (imaginative processing)

These commands allow manual intervention or debugging of Astra’s inner world.

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-04-14
"""

from beta.services import state_service


async def dinner_summary(ctx):
    """📜 Summarizes unresolved dinner topics in Astra's journal."""
    summary = state_service.get_dinner_summary()
    await ctx.send(summary)

dinner_summary._is_command = True
dinner_summary.category = "⏳ State"


async def dinner_answer(ctx, *, response: str):
    """📝 Records a user’s reply to Astra’s current dinner prompt."""
    from astra_core.dinner.dinner_journal import load_dinner_journal, mark_dinner_responded
    from astra_core.astra_schedule.dinner import try_resolve_dinner_topic

    journal = load_dinner_journal()
    latest = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)

    if not latest:
        await ctx.send("⚠️ No unresolved dinner topic found.")
        return

    topic = latest["content"]
    timestamp = latest["timestamp"]  # 👈 ensure accurate match

    # 🧠 Save response using exact topic+timestamp
    mark_dinner_responded(topic, "user", response, timestamp=timestamp)
    await ctx.send("✅ Got your dinner reply. Astra will reflect soon.")

    # ✅ Try to resolve immediately
    await try_resolve_dinner_topic(latest, ctx.channel)



dinner_answer._is_command = True
dinner_answer.category = "⏳ State"


async def resolve_dinner(ctx):
    """🎓 Resolves all dinner topics with complete co-parent responses."""
    await state_service.resolve_all_dinner_topics(send_func=ctx.send)

resolve_dinner._is_command = True
resolve_dinner.category = "⏳ State"


async def dinnertime(ctx):
    """🍽️ Manually initiates Astra’s full dinner reflection loop."""
    await ctx.send("🍽️ Calling Astra to the dinner table...")
    await state_service.start_dinner(ctx.bot, ctx.channel.id)

dinnertime._is_command = True
dinnertime.category = "⏳ State"


async def playtime(ctx):
    """🎮 Starts a creative exploration cycle during playtime."""
    await ctx.send("🎮 Astra is entering Play Mode...")
    thoughts = await state_service.run_playtime()
    for thought in thoughts:
        await ctx.send(thought)

playtime._is_command = True
playtime.category = "⏳ State"


async def dreamtime(ctx):
    """🌙 Triggers a one-off dreaming session and logs reflections."""
    await ctx.send("🌙 Entering dream mode...")
    final_message = await state_service.run_dreamtime()
    await ctx.send(final_message)

dreamtime._is_command = True
dreamtime.category = "⏳ State"


async def dinner_topic(ctx, *, topic: str):
    """📝 Adds a co-parent initiated topic to Astra’s dinner journal."""
    from astra_core.dinner.dinner_journal import save_dinner_topic

    save_dinner_topic(
        topic_text=topic,
        topic_type="reflection",
        status="unresolved",
        source="co-parent"
    )
    await ctx.send(f"📝 Topic added to dinner journal: “{topic}”")

dinner_topic._is_command = True
dinner_topic.category = "⏳ State"


async def dinner_debug(ctx):
    """🔍 Debug Astra's most recent dinner topic in raw JSON."""
    from astra_core.dinner.dinner_journal import load_dinner_journal
    from beta.services import state_service
    import json

    journal = load_dinner_journal()
    if not journal:
        await ctx.send("📭 Dinner journal is empty.")
        return

    last = journal[-1]
    raw_json = json.dumps(last, indent=2)

    await state_service.send_chunked_message(
        ctx.send,
        raw_json,
        prefix="🧾 Most recent dinner entry:\n```json\n",
    )

dinner_debug._is_command = True
dinner_debug.category = "⏳ State"
