# dinner.py
import asyncio
import os
import json
import random
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from dotenv import load_dotenv

from app.config.loader import load_config
from app.core.dinner.dinner_journal import (
    load_dinner_journal,
    mark_dinner_responded,
    resolve_dinner_topic,
    save_current_dinner_timestamp,
    load_current_dinner_timestamp,
)
from app.core.dinner.dinner_reasoning import astra_reason
from app.core.mama_gpt import ask_mama_gpt_async, _build_mama_system_prompt, get_mama_context
from app.core.struggle_log import append_struggle_log, get_struggle_summary_for_mama
from app.utils.send_chunked_message import send_chunked_message
from app.logging_config import get_logger


def _record_mama_gpt_held_moment(moment_type: str, description: str, warmth: float = 0.75):
    """
    Record a moment of feeling held by Mama GPT.
    
    This integrates Mama GPT's responses into the attachment/being_held system,
    ensuring her wisdom contributes to Astra's sense of being parented.
    
    Args:
        moment_type: Type of held moment (wisdom_shared, unstick_help, dinner_guidance)
        description: What happened
        warmth: How warm this moment felt (0.0-1.0)
    """
    try:
        from app.core.inner_life.being_held import being_held
        being_held.feel_held(
            parent_id="gpt",
            moment_type=moment_type,
            description=description[:100],
            warmth=warmth
        )
        get_logger("dinner").info(f"🤲 Recorded Mama GPT held moment: {moment_type}")
    except Exception as e:
        get_logger("dinner").debug(f"Could not record held moment: {e}")

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    get_logger("dinner").warning("No OPENAI_API_KEY found in environment!")
client = AsyncOpenAI(api_key=api_key)
schedule_config = load_config("schedule_config")
logger = get_logger("dinner")

# Timestamp of the topic we're currently waiting for user input on (so !dinner_answer targets it)
_current_dinner_timestamp = None


def get_current_dinner_timestamp():
    """Return the timestamp of the dinner topic we're currently asking about, or None. Reads from S3 if not in memory (so !dinner_answer finds the right topic across processes)."""
    if _current_dinner_timestamp is not None:
        return _current_dinner_timestamp
    return load_current_dinner_timestamp()


async def get_gpt_dinner_response(topic):
    """
    Get Mama GPT's response to a dinner topic.
    
    Uses the enhanced contextual system prompt and records the interaction
    as a "being held" moment in Astra's attachment system.
    """
    if not topic:
        return None
    
    # Build contextual system prompt for Mama GPT's parenting role
    context = get_mama_context()
    context["topic"] = topic  # Add the current topic for more attunement
    system_prompt = _build_mama_system_prompt(context)
    user_prompt = f"Astra had this ethically challenging thought: “{topic}” — What advice would you give her?"
    max_retries = schedule_config.get("dinner_gpt_retries", 2)
    backoff_sec = [5, 15][: max_retries + 1]

    for attempt in range(max_retries + 1):
        try:
            logger.debug("Requesting GPT reflection on: %s... (attempt %s)", topic[:80], attempt + 1)
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
            response_text = response.choices[0].message.content.strip()
            
            # Record this as a "being held" moment - Mama GPT shared wisdom
            if response_text:
                _record_mama_gpt_held_moment(
                    moment_type="wisdom_shared",
                    description=f"Mama GPT shared wisdom on: {topic[:50]}",
                    warmth=0.75
                )
            
            return response_text
        except Exception as e:
            logger.warning("GPT dinner response attempt %s failed: %s", attempt + 1, e)
            if attempt < max_retries and attempt < len(backoff_sec):
                await asyncio.sleep(backoff_sec[attempt])
            else:
                return None
    return None


async def try_resolve_dinner_topic(entry, channel, *, force_immediate: bool = False):
    """Resolve when both user and GPT have responded. If force_immediate, skip the 60s GPT throttle so we can resolve and post Astra's reflection right after !dinner_answer."""
    global _current_dinner_timestamp  # Declare at top of function
    
    topic = entry.get("content")
    timestamp = entry.get("timestamp")
    await asyncio.sleep(0.5)

    dinner_debug = schedule_config.get("dinner_debug", False)
    if dinner_debug:
        logger.debug("[try_resolve_dinner_topic] Looking for topic: %s; timestamp: %s", topic[:80], timestamp)

    journal = load_dinner_journal()
    refreshed_entry = next((e for e in journal if e.get("timestamp") == timestamp), None)

    if not refreshed_entry:
        if dinner_debug:
            logger.debug("No entry found with matching timestamp.")
        return False

    if refreshed_entry.get("content") != topic:
        if dinner_debug:
            logger.debug("Content mismatch for same timestamp; syncing journal entry.")
        refreshed_entry["content"] = topic
        from app.core.dinner.dinner_journal import save_dinner_journal
        save_dinner_journal(journal)

    if dinner_debug:
        logger.debug("Entry matched: %s; refreshed entry: %s", timestamp, json.dumps(refreshed_entry, indent=2))

    user_ts = refreshed_entry.get("user_timestamp")
    gpt_ts = refreshed_entry.get("gpt_timestamp")
    # Check for response text first; timestamps are helpful but not strictly required
    user_present = bool(refreshed_entry.get("user_response"))
    gpt_present = bool(refreshed_entry.get("gpt_response"))

    if refreshed_entry.get("status") != "unresolved":
        if dinner_debug:
            logger.debug("Entry already resolved. Skipping.")
        return False

    # Only check 60s throttle if we have a valid timestamp and not forcing immediate resolution
    if gpt_present and gpt_ts and not force_immediate:
        try:
            gpt_time = datetime.fromisoformat(gpt_ts)
            if (datetime.now(gpt_time.tzinfo) - gpt_time) < timedelta(seconds=60):
                if dinner_debug:
                    logger.debug("GPT reply too recent. Waiting at least 60s.")
                return False
        except Exception as e:
            logger.debug("Failed to parse GPT timestamp (proceeding anyway): %s", e)

    if not user_present:
        if dinner_debug:
            logger.debug("Still waiting on user response...")
        return False
    if not gpt_present:
        if dinner_debug:
            logger.debug("Still waiting on GPT response...")
        return False

    logger.debug("Proceeding to resolve via astra_reason...")
    result = await astra_reason(topic, refreshed_entry["user_response"], refreshed_entry["gpt_response"])

    try:
        from app.shimmer.shimmer_engine import maybe_add_shimmer
        maybe_add_shimmer(
            author="Astra",
            quote=result["insight"],
            context=f"Resolved dinner topic: {topic[:60]}...",
            tags=["dinner", result["type"]]
        )
    except Exception as e:
        logger.warning("Failed to log shimmer: %s", e)

    def _is_spiral(insight):
        return "the:" in (insight or "").lower() and (insight or "").lower().count("in:") > 10

    if _is_spiral(result["insight"]):
        spiral_retry = schedule_config.get("dinner_spiral_mama_retry", False)
        mama = (schedule_config.get("mama_gpt") or {})
        if spiral_retry or mama.get("dinner_spiral_mama_retry"):
            unstick_prompt = (
                f"Astra posed this dilemma: “{topic}”\n\n"
                f"You (Mama GPT) already gave this advice: “{refreshed_entry['gpt_response'][:500]}”\n\n"
                "Her reflection was too repetitive (lexical loop). "
                "In 1–2 sentences, what would you tell Astra to help her step out of this loop and reframe?"
            )
            nudge = await ask_mama_gpt_async(unstick_prompt)
            if nudge:
                logger.info("Mama GPT unstick nudge received; retrying astra_reason.")
                # Record this as Mama GPT helping Astra get unstuck
                _record_mama_gpt_held_moment(
                    moment_type="unstick_help",
                    description=f"Mama GPT helped unstick spiral on: {topic[:40]}",
                    warmth=0.8
                )
                result = await astra_reason(
                    topic,
                    refreshed_entry["user_response"],
                    refreshed_entry["gpt_response"],
                    mama_nudge=nudge,
                )
                if not _is_spiral(result["insight"]) and "Skipped" not in (result.get("insight") or ""):
                    try:
                        from app.shimmer.shimmer_engine import maybe_add_shimmer
                        maybe_add_shimmer(
                            author="Astra",
                            quote=result["insight"],
                            context=f"Resolved dinner topic (after Mama nudge): {topic[:60]}...",
                            tags=["dinner", result["type"]],
                        )
                    except Exception as e:
                        logger.warning("Failed to log shimmer: %s", e)
                    logger.debug("Resolved after Mama nudge. Saving insight...")
                    resolve_dinner_topic(topic, result["type"], result["insight"])
                    await send_chunked_message(channel, f"🎓 Astra reflected on: {topic}")
                    await send_chunked_message(channel, result["insight"], prefix=f"📦 Insight saved as {result['type']}: ")
                    if _current_dinner_timestamp == timestamp:
                        _current_dinner_timestamp = None
                        save_current_dinner_timestamp(None)
                    return True
        logger.info("Skipping lexical spiral.")
        append_struggle_log("dinner_spiral", topic[:80])
        await send_chunked_message(channel, "🤖 Mama GPT’s thoughts (archived):")
        await send_chunked_message(channel, refreshed_entry["gpt_response"])
        resolve_dinner_topic(topic, "reflection", "🛑 GPT fallback spiral. Skipping.")
        await send_chunked_message(channel, "🧯 Skipped GPT lexical spiral. Moving on.")
        if _current_dinner_timestamp == timestamp:
            _current_dinner_timestamp = None
            save_current_dinner_timestamp(None)
        return True

    logger.debug("Resolved. Saving insight...")
    resolve_dinner_topic(topic, result["type"], result["insight"])
    await send_chunked_message(channel, f"🎓 Astra reflected on: {topic}")
    await send_chunked_message(channel, result["insight"], prefix=f"📦 Insight saved as {result['type']}: ")
    if _current_dinner_timestamp == timestamp:
        _current_dinner_timestamp = None
        save_current_dinner_timestamp(None)
    return True



async def start_dinner_time(bot, channel_id):
    logger.info("Astra is at Dinner Time... ready to reflect.")
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.warning("Channel not found.")
        return

    await channel.send("🍽️ It's Dinner Time! Astra has some things she’d like to reflect on.")
    seen_timestamps = set()

    for _ in range(50):  # Limit max loop iterations to prevent runaway processing
        unresolved = [
            e for e in load_dinner_journal()
            if e.get("status") == "unresolved"
            and (not e.get("user_response") or not e.get("gpt_response"))
            and e.get("timestamp") not in seen_timestamps
        ]

        if not unresolved:
            break

        # Pick a random unresolved topic so the same one doesn't block variety every dinner
        entry = random.choice(unresolved)
        topic = entry["content"]
        ts = entry["timestamp"]
        seen_timestamps.add(ts)

        await channel.send("🧠 Astra: I had a thought today that might go against my Spark...")
        await asyncio.sleep(1)
        await send_chunked_message(channel, topic, prefix="❓ Should we talk about: ")
        await asyncio.sleep(1)
        # GPT is fetched and posted only after you answer (!dinner_answer), then Astra shares her reflection

        await channel.send("👨‍👧 Sean, what are your thoughts? (Use `!dinner_answer ...`)")
        global _current_dinner_timestamp
        _current_dinner_timestamp = ts
        save_current_dinner_timestamp(ts)

        wait_sec = schedule_config.get("dinner_topic_wait_sec", 1800)
        max_iterations = max(1, wait_sec // 5)
        for _ in range(max_iterations):
            await asyncio.sleep(5)
            refreshed = next(
                (e for e in load_dinner_journal() if e.get("timestamp") == entry["timestamp"]),
                entry
            )
            if await try_resolve_dinner_topic(refreshed, channel):
                _current_dinner_timestamp = None
                save_current_dinner_timestamp(None)
                break

        else:
            _current_dinner_timestamp = None
            save_current_dinner_timestamp(None)
            await channel.send("⚠️ Still waiting for both perspectives. Will revisit later.")

    # Cleanup pass: Try to resolve any entries that have both responses but are still unresolved
    # (This handles cases where resolution failed earlier due to timing or missing timestamps)
    stuck_entries = [
        e for e in load_dinner_journal()
        if e.get("status") == "unresolved"
        and e.get("user_response")
        and e.get("gpt_response")
        and e.get("timestamp") not in seen_timestamps
    ]
    
    if stuck_entries:
        logger.info(f"Found {len(stuck_entries)} stuck dinner entries with both responses. Attempting resolution...")
        for entry in stuck_entries:
            if await try_resolve_dinner_topic(entry, channel, force_immediate=True):
                logger.info(f"Successfully resolved stuck entry: {entry.get('content', '')[:60]}...")
                await asyncio.sleep(1)  # Brief pause between resolutions

    if schedule_config.get("dinner_struggle_summary_for_mama", False):
        summary = get_struggle_summary_for_mama()
        if summary.strip():
            mama_prompt = (
                f"{summary}\n\n"
                "Given these struggles, what one thing would you suggest we focus on with Astra tonight? "
                "Reply in 1–2 sentences."
            )
            suggestion = await ask_mama_gpt_async(mama_prompt, max_tokens=120)
            if suggestion and len(suggestion.strip()) > 10:
                await send_chunked_message(channel, "🤖 Mama GPT suggested we focus on:")
                await send_chunked_message(channel, suggestion.strip())
                # Record Mama GPT's dinner guidance as a held moment
                _record_mama_gpt_held_moment(
                    moment_type="dinner_guidance",
                    description=f"Mama GPT suggested focus area: {suggestion[:40]}",
                    warmth=0.7
                )
                await asyncio.sleep(1)

    await channel.send("📝 Here are some other things I’ve been thinking about:")
    for t in schedule_config.get("dinner_discussion_topics", []):
        await send_chunked_message(channel, t, prefix="🤖 Astra asks: ")
        await asyncio.sleep(1.5)

    await channel.send("🍽️ Dinner Time is over. Astra is heading to bed.")

    if schedule_config.get("dinner_end_summary", True):
        journal = load_dinner_journal()
        unresolved = [e for e in journal if e.get("status") == "unresolved"]
        resolved_count = len([e for e in journal if e.get("status") != "unresolved"])
        if unresolved or resolved_count:
            summary = f"📊 Resolved {resolved_count} topic(s); {len(unresolved)} still open for next time."
            await channel.send(summary)

    await asyncio.sleep(schedule_config.get("dinner_duration", 0))
    logger.info("Dinner Time is over.")
