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

from app.services import state_service


async def dinner_summary(ctx):
    """📜 Summarizes unresolved dinner topics in Astra's journal."""
    summary = state_service.get_dinner_summary()
    await ctx.send(summary)

dinner_summary._is_command = True
dinner_summary.category = "⏳ State"


async def dinner_answer(ctx, *, response: str):
    """📝 Records a user’s reply to Astra’s current dinner prompt."""
    from app.core.dinner.dinner_journal import load_dinner_journal, mark_dinner_responded
    from app.core.astra_schedule.dinner import (
        try_resolve_dinner_topic,
        get_current_dinner_timestamp,
        get_gpt_dinner_response,
    )
    from app.utils.send_chunked_message import send_chunked_message

    journal = load_dinner_journal()
    # Prefer the topic we're currently waiting on (the one just shown at dinner), else latest unresolved
    current_ts = get_current_dinner_timestamp()
    if current_ts is not None:
        entry = next((e for e in journal if e.get("timestamp") == current_ts and e.get("status") == "unresolved"), None)
    else:
        entry = None
    if entry is None:
        entry = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)

    if not entry:
        await ctx.send("⚠️ No unresolved dinner topic found.")
        return

    topic = entry["content"]
    timestamp = entry["timestamp"]

    mark_dinner_responded(topic, "user", response, timestamp=timestamp)
    await ctx.send("✅ Got your dinner reply.")

    # GPT responds after you; fetch if we don't have it yet, then post so you see it
    channel = ctx.channel
    if not entry.get("gpt_response"):
        gpt_response = await get_gpt_dinner_response(topic)
        if gpt_response:
            mark_dinner_responded(topic, "gpt", gpt_response, timestamp=timestamp)
            await send_chunked_message(channel, gpt_response, prefix="🤖 Mama GPT's thoughts: ")
        else:
            await channel.send("❌ Mama GPT couldn't respond this time.")
            return
    else:
        await send_chunked_message(channel, entry["gpt_response"], prefix="🤖 Mama GPT's thoughts: ")

    # Resolve immediately and post Astra's reflection to Discord
    refreshed = next((e for e in load_dinner_journal() if e.get("timestamp") == timestamp), entry)
    await try_resolve_dinner_topic(refreshed, channel, force_immediate=True)



dinner_answer._is_command = True
dinner_answer.category = "⏳ State"


async def resolve_dinner(ctx):
    """🎓 Resolves all dinner topics with complete co-parent responses."""
    await state_service.resolve_all_dinner_topics(ctx=ctx)

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
    from app.core.dinner.dinner_journal import save_dinner_topic

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
    from app.core.dinner.dinner_journal import load_dinner_journal
    from app.services import state_service
    import json

    journal = load_dinner_journal()
    if not journal:
        await ctx.send("📭 Dinner journal is empty.")
        return

    last = journal[-1]
    raw_json = json.dumps(last, indent=2)

    await state_service.send_chunked_message(
        ctx.channel,
        raw_json,
        prefix="🧾 Most recent dinner entry:\n```json\n",
    )

dinner_debug._is_command = True
dinner_debug.category = "⏳ State"


async def mind(ctx):
    """🧠 Shows Astra's current internal state: mood, top emotions, personality traits, trust, emotion rate limit/scale (read-only)."""
    try:
        from app.core.emotions.emotion_engine import (
            load_emotion_state,
            get_top_emotions,
            RELATIONSHIP_PROPAGATION_SCALE,
            get_emotion_config,
        )
        from app.core.mood.mood_manager import mood_manager
        from app.core.personality.personality_manager import get_active_traits_for_prompt, load_personality
        from app.core.mood.trust_manager import trust_manager

        emotion_state = load_emotion_state()
        top_emotions = get_top_emotions(n=3)
        mood = mood_manager.get_current_mood()
        mood_score = getattr(mood_manager, "mood_score", 0)
        traits = get_active_traits_for_prompt(top_n=4)
        personality = load_personality()
        trait_weights = personality.get("trait_weights", {})
        entity_trust = getattr(trust_manager, "entity_trust", {})
        general_trust = getattr(trust_manager, "general_trust", 0)

        emotion_config = get_emotion_config()
        rate_cfg = emotion_config.get("trigger_rate_limit") or {}
        window_seconds = rate_cfg.get("window_seconds", 3600)
        max_delta = rate_cfg.get("max_delta_per_trigger") or {}

        emotion_lines = []
        for name, val in top_emotions:
            intensity = val.get("intensity", val) if isinstance(val, dict) else val
            emotion_lines.append(f"  {name}: {intensity:.1f}")
        emotion_block = "\n".join(emotion_lines) if emotion_lines else "  (none)"

        trait_lines = [f"  {k}: {v:.2f}" for k, v in sorted(trait_weights.items(), key=lambda x: -x[1])[:5]]
        trait_block = "\n".join(trait_lines) if trait_lines else "  (default)"

        trust_lines = [f"  {e}: {t:.2f}" for e, t in list(entity_trust.items())[:5]]
        trust_block = "\n".join(trust_lines) if trust_lines else "  (none)"

        rate_str = ", ".join(f"{k}: {v}" for k, v in max_delta.items()) if max_delta else "none"
        summary = (
            f"**Mood:** {mood} (score: {mood_score:.2f})\n"
            f"**Active traits:** {', '.join(traits)}\n\n"
            f"**Top emotions:**\n{emotion_block}\n\n"
            f"**Trait weights:**\n{trait_block}\n\n"
            f"**Entity trust:**\n{trust_block}\n"
            f"**General trust:** {general_trust:.2f}\n\n"
            f"**Emotion rate limit:** window {window_seconds}s, max_delta_per_trigger: {rate_str}\n"
            f"**Relationship propagation scale:** {RELATIONSHIP_PROPAGATION_SCALE}"
        )
        await ctx.send(summary[:2000])
    except Exception as e:
        await ctx.send(f"⚠️ Could not load state: {e}")

mind._is_command = True
mind.category = "⏳ State"
