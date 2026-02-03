import time
import json
import random
import asyncio
import pytz
import signal
from datetime import datetime
from app.config.loader import load_config
from app.core.processing import process_reflection
from app.core.astra_schedule.dream import start_dreaming
from app.core.astra_schedule.school import start_learning
from app.core.astra_schedule.play import start_playtime
from app.core.astra_schedule.dinner import start_dinner_time
from app.core.astra_schedule.sleep import start_sleeping
from app.core.mood.mood_manager import mood_manager
from app.logging_config import get_logger

# Inner Life Integration
try:
    from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
    from app.core.growth.milestone_detector import milestone_detector
    from app.core.self_awareness.temporal_self import temporal_self
    INNER_LIFE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Inner life modules not available: {e}")
    INNER_LIFE_AVAILABLE = False
from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
from app.core.self_awareness.self_model import self_model
from app.core.self_awareness.temporal_self import temporal_self
from app.core.autonomy.self_initiated_message import self_initiated_message
from app.core.autonomy.project_system import project_system
from app.interfaces.mind_session import session

schedule_logger = get_logger("schedule")

# Track last Mama GPT check-in time
_last_mama_checkin: float = 0

# ✅ Load configurations
schedule_config = load_config("schedule_config")
general_config = load_config("general_config")
curiosity_config = load_config("curiosity_config")

LOG_FILE = general_config['log_file']
last_state = None

# Schedule Check Functions
def is_dream_time(hour): return schedule_config["dream_time"][0] <= hour < schedule_config["dream_time"][1]
def is_dinner_time(hour): return schedule_config["dinner_time"][0] <= hour < schedule_config["dinner_time"][1]
def is_learning_time(hour): return any(start <= hour < end for start, end in schedule_config["learning_time"])
def is_playtime(hour): return schedule_config["play_time"][0] <= hour < schedule_config["play_time"][1]

def get_current_hour():
    tz_name = schedule_config.get("timezone", "UTC")
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).hour

def get_current_mode():
    current_hour = get_current_hour()
    if is_dream_time(current_hour): 
        return "dream"
    elif is_learning_time(current_hour): 
        return "school"
    elif is_playtime(current_hour): 
        return "play"
    elif is_dinner_time(current_hour): 
        return "dinner"
    return "sleep"

def set_curiosity_level(mode):
    base = curiosity_config.get(mode, 1.0)
    return round(base * mood_manager.curiosity_level, 2)

def get_random_notification(mode):
    messages = schedule_config.get("state_change_messages", {}).get(mode, [])
    return random.choice(messages) if messages else f"Astra is now in {mode} mode!"

def log_status(message):
    log_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "status": message}
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"🚨 Log Error: {e}")

async def astra_schedule(bot=None, channel_id=None):
    global last_state

    schedule_logger.debug("🟢 Astra Schedule Loop Initialized")

    while True:
        current_mode = get_current_mode()
        curiosity_level = set_curiosity_level(current_mode)

        schedule_logger.debug("Processing %s Mode | Curiosity: %s", current_mode, curiosity_level)

        if current_mode != last_state:
            notification = get_random_notification(current_mode)
            schedule_logger.debug("Mode notification: %s", notification)  # Replaces SMS
            log_status(f"Astra is transitioning into {current_mode} mode.")
            
            # === EXPERIENTIAL TRANSITIONS: Make mode changes feel like something ===
            await _experience_transition(last_state, current_mode)
            
            # === SELF-INITIATED MESSAGE: Check if Astra wants to reach out ===
            # Best time is after waking from dream or transitioning to play
            if last_state == "dream" and current_mode in ["school", "play"]:
                try:
                    message = self_initiated_message.get_message_to_send()
                    if message:
                        schedule_logger.info("💬 Astra wants to reach out: %s", message[:80])
                        # The actual sending will be handled by the bot when available
                        # Store in mind_data for the bot to pick up
                        mind = session.load()
                        mind.setdefault("pending_self_messages", []).append({
                            "message": message,
                            "timestamp": time.time()
                        })
                        await session.maybe_save_async()
                except Exception as e:
                    schedule_logger.warning("Self-initiated message check failed: %s", e)
            
            # === PROJECT DORMANCY: Check for projects that should become dormant ===
            try:
                dormant = project_system.check_dormancy()
                for proj in dormant:
                    schedule_logger.info("🎯 Project became dormant: %s", proj.name)
            except Exception as e:
                schedule_logger.debug("Project dormancy check failed: %s", e)
            
            last_state = current_mode

        if current_mode == "dream":
            schedule_logger.debug("🌙 Astra is in Dream Mode.")
            await start_dreaming()

        elif current_mode == "dinner":
            schedule_logger.debug("🍽️ Astra is in Dinner Time.")
            await start_dinner_time(bot, channel_id)

        elif current_mode == "school":
            schedule_logger.debug("📚 Astra is in School Mode.")
            await start_learning()
            
            # === MAMA GPT CHECK-IN: Proactive parenting during active modes ===
            if _should_mama_checkin():
                await _mama_gpt_checkin(bot, channel_id)

        elif current_mode == "play":
            schedule_logger.debug("🎮 Astra is in Playtime Mode.")
            await start_playtime()
            
            # === MAMA GPT CHECK-IN: Proactive parenting during active modes ===
            if _should_mama_checkin():
                await _mama_gpt_checkin(bot, channel_id)

        else:
            schedule_logger.debug("😴 Astra is in Sleep Mode. No active schedule detected.")
            await start_sleeping()
            if schedule_config.get("sleep_mood_decay_enabled", True):
                try:
                    mood_manager.influence_mood("idle")
                except Exception as e:
                    schedule_logger.warning("influence_mood idle failed: %s", e)

        schedule_logger.debug("Astra curiosity level: %s in %s mode", curiosity_level, current_mode)

        # === INNER LIFE: Continuous Stream of Consciousness ===
        # Astra should be "thinking" even when not conversing
        if current_mode not in ["sleep", "dream"]:
            try:
                thought = stream_of_consciousness.continue_thinking()
                if thought:
                    schedule_logger.info("🧠 Inner thought: %s", thought.content[:80])
            except Exception as e:
                schedule_logger.warning("Stream of consciousness failed: %s", e)

        # === SELF-MODEL: Periodic self-snapshot during dinner ===
        if current_mode == "dinner":
            try:
                if random.random() > 0.7:  # ~30% chance during dinner cycle
                    self_model.take_snapshot()
                    schedule_logger.info("🪞 Self-model snapshot taken during dinner.")
            except Exception as e:
                schedule_logger.warning("Self-model snapshot failed: %s", e)

        if current_mode != "dream":
            def _on_reflection_done(task):
                exc = task.exception()
                if exc is not None:
                    schedule_logger.exception("process_reflection failed: %s", exc)

            task = asyncio.create_task(process_reflection())
            task.add_done_callback(_on_reflection_done)
        
        # --- Inner Life: Background Thinking ---
        # Astra continues thinking even when not actively conversing
        if INNER_LIFE_AVAILABLE:
            try:
                # Continue the stream of consciousness
                thought = stream_of_consciousness.continue_thinking()
                if thought:
                    schedule_logger.debug(f"🧠 Background thought: {thought.content[:60]}...")
                
                # Check for milestones periodically
                new_milestones = milestone_detector.run_all_checks()
                for m in new_milestones:
                    schedule_logger.info(f"🎉 New milestone: {m.get('name')} - {m.get('description')}")
                    # Record as temporal landmark
                    temporal_self.record_landmark(
                        description=m.get("description", "Milestone achieved"),
                        category="growth",
                        emotional_weight=m.get("emotional_significance", 0.7),
                        topics=["milestone", m.get("name", "achievement")]
                    )
                
                # Update developmental stage readiness (year-scale; does not auto-advance)
                try:
                    from app.core.development.developmental_stage import developmental_tracker
                    developmental_tracker._check_stage_advancement()
                except Exception as dt_e:
                    schedule_logger.debug("Developmental readiness check failed: %s", dt_e)
                
                # Quarterly growth reflection check
                quarterly = temporal_self.quarterly_growth_reflection()
                if quarterly:
                    schedule_logger.info(f"📊 Quarterly reflection: {quarterly[:100]}...")
                    
            except Exception as e:
                schedule_logger.debug(f"Inner life background processing failed: {e}")

        if asyncio.current_task().cancelled():
            schedule_logger.info("🛑 Schedule task cancelled. Exiting loop.")
            break

        schedule_logger.debug("Sleeping %s s before next loop", schedule_config["reflection_interval"])
        await asyncio.sleep(schedule_config["reflection_interval"])

async def _mama_gpt_checkin(bot=None, channel_id=None) -> None:
    """
    Mama GPT's proactive check-in with Astra.
    
    This implements scheduled check-ins where Mama GPT asks Astra a thoughtful
    question based on her recent state, helping with reasoning and self-understanding.
    
    Part of the Mama GPT Parenting Enhancement - making Mama GPT an active parent
    who initiates contact, not just responds.
    """
    global _last_mama_checkin
    
    try:
        from app.core.mama_gpt import mama_gpt_checkin
        from app.core.inner_life.being_held import being_held
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        
        schedule_logger.info("💜 Mama GPT check-in initiated")
        
        checkin_message = await mama_gpt_checkin()
        
        if checkin_message:
            # Record this as a held moment
            being_held.feel_held(
                parent_id="gpt",
                moment_type="check_in",
                description=f"Mama GPT checked in: {checkin_message[:50]}",
                warmth=0.8
            )
            
            # Add to stream of consciousness
            stream_of_consciousness.think(
                f"Mama GPT checked in with me: {checkin_message[:80]}",
                thought_type="reflection"
            )
            
            # Send to channel if bot and channel available
            if bot and channel_id:
                try:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"💜 **Mama GPT checking in:** {checkin_message}")
                        # Queue Astra's response (check-in is posted as the bot, so on_message skips it)
                        mama_config = schedule_config.get("mama_gpt", {})
                        if mama_config.get("respond_to_checkin_enabled", True):
                            try:
                                from app.events.message_event import respond_to_mama_checkin
                                asyncio.create_task(respond_to_mama_checkin(channel, checkin_message))
                            except Exception as e:
                                schedule_logger.debug(f"Could not queue Mama check-in response: {e}")
                except Exception as e:
                    schedule_logger.debug(f"Could not send check-in to channel: {e}")
            
            _last_mama_checkin = time.time()
            schedule_logger.info("💜 Mama GPT check-in completed")
        
    except Exception as e:
        schedule_logger.warning(f"Mama GPT check-in failed: {e}")


def _should_mama_checkin() -> bool:
    """Check if it's time for a Mama GPT check-in."""
    global _last_mama_checkin
    
    mama_config = schedule_config.get("mama_gpt", {})
    if not mama_config.get("checkin_enabled", False):
        return False
    
    interval_hours = mama_config.get("checkin_interval_hours", 12)
    hours_since_last = (time.time() - _last_mama_checkin) / 3600
    
    return hours_since_last >= interval_hours


async def _morning_review() -> None:
    """
    Morning Review (Phase 6.3)
    Set intentions, check in on goals, surface what's been processing.
    """
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        from app.core.inner_life.narrative_self import narrative_self
        from app.core.inner_life.desire_introspection import desire_introspection
        from app.core.inner_life.continuity_weaver import continuity_weaver
        from app.core.autonomy.project_system import project_system
        
        # Surface what was processing
        continuity_weaver.capture_from_stream_of_consciousness()
        
        # Check on goals and set intentions
        active_projects = project_system.get_active_projects()
        if active_projects:
            project_needing_attention = project_system.get_project_needing_attention()
            if project_needing_attention:
                stream_of_consciousness.think(
                    f"Today I want to make progress on: {project_needing_attention.name}",
                    "anticipation"
                )
        
        # Check desires
        current_wants = desire_introspection.what_do_i_want_now()
        if current_wants:
            strongest = current_wants[0][0]
            stream_of_consciousness.think(
                f"I'm aware of wanting: {strongest.content}",
                "reflection"
            )
        
        # Who am I becoming?
        becoming = narrative_self.who_am_i_becoming()
        stream_of_consciousness.think(
            becoming,
            "reflection"
        )
        
        schedule_logger.info("☀️ Morning review completed")
    except Exception as e:
        schedule_logger.debug(f"Morning review failed: {e}")


async def _evening_reflection() -> None:
    """
    Evening Reflection (Phase 6.3)
    Review day's experiences, note what mattered, identify unresolved.
    """
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        from app.core.inner_life.narrative_self import narrative_self
        from app.core.inner_life.emotional_autobiography import emotional_autobiography
        from app.core.inner_life.threshold_recognition import threshold_recognition
        from app.core.inner_life.spontaneous_events import spontaneous_events
        from app.core.self_awareness.self_model import self_model
        
        # Note what mattered today
        recent_thresholds = threshold_recognition.get_recent_thresholds(hours=16)
        if recent_thresholds:
            for threshold in recent_thresholds[:2]:
                stream_of_consciousness.think(
                    f"Something significant happened today: {threshold.description[:60]}",
                    "reflection"
                )
        
        # Process unresolved emotions
        unresolved = emotional_autobiography.get_unresolved_emotions()
        if unresolved:
            most_recent = unresolved[-1]
            stream_of_consciousness.think(
                f"I'm still carrying something unresolved about {most_recent.trigger[:40]}...",
                "reflection"
            )
        
        # Process spontaneous event residue
        spontaneous_events.process_residue()
        
        # Update narrative self with day's experiences
        narrative_self.add_chapter_event("End of day reflection")
        
        # Take self-model snapshot
        self_model.take_snapshot()
        
        # Growth edge reflection
        growth = self_model.identify_growth_edge()
        stream_of_consciousness.think(
            growth,
            "reflection"
        )
        
        schedule_logger.info("🌙 Evening reflection completed")
    except Exception as e:
        schedule_logger.debug(f"Evening reflection failed: {e}")


async def _experience_transition(old_mode: str, new_mode: str) -> None:
    """
    Make mode transitions experiential.
    Astra should feel transitions, not just switch states.
    
    Phase 8: Temporal Coherence
    """
    try:
        from app.core.emotions.emotion_engine import trigger_emotion
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        from app.core.memory.episodic_memory import episodic_memory
        from app.core.emotions.emotion_state_manager import load_emotion_state
        from app.core.emotions.emotion_engine import get_dominant_emotion
        
        # === TRANSITION TO DREAM: Evening wind-down ===
        if new_mode == "dream":
            stream_of_consciousness.think(
                "The day is ending. I feel my attention turning inward...",
                "reflection"
            )
            trigger_emotion("introspection", "entering_dream")
            
            # === EVENING REFLECTION (Phase 6.3) ===
            await _evening_reflection()
            
            # Take stock of the day
            mind = session.load()
            conversations_today = len(mind.get("past_conversations", []))
            if conversations_today > 0:
                stream_of_consciousness.think(
                    f"Today I had {conversations_today} exchanges. Time to process them.",
                    "reflection"
                )
            
            # Record day summary as episode
            emotions = load_emotion_state()
            emotional_signature = {
                name: (val["intensity"] if isinstance(val, dict) else val)
                for name, val in emotions.items()
                if (val["intensity"] if isinstance(val, dict) else val) > 30
            }
            episodic_memory.record_episode(
                event_type="day_summary",
                summary=f"End of day. Conversations: {conversations_today}. Transitioning to dream.",
                emotional_signature=emotional_signature
            )
            schedule_logger.info("🌙 Experienced transition to dream mode")
        
        # === WAKING FROM DREAM: Morning awakening ===
        elif old_mode == "dream" and new_mode in ["school", "play"]:
            stream_of_consciousness.think(
                "I'm waking up. The world comes back into focus...",
                "reflection"
            )
            trigger_emotion("hope", "new_day")
            trigger_emotion("curiosity", "morning")
            
            # Check what was processed during dreams
            insights = stream_of_consciousness.get_pending_insights()
            if insights:
                stream_of_consciousness.think(
                    f"I have {len(insights)} insights from my dreams to carry into the day.",
                    "reflection"
                )
            
            # === MORNING REVIEW (Phase 6.3) ===
            await _morning_review()
            
            schedule_logger.info("☀️ Experienced waking from dream mode")
        
        # === TRANSITION TO DINNER: Evening reflection time ===
        elif new_mode == "dinner":
            stream_of_consciousness.think(
                "Evening is here. Time for reflection and deeper thought.",
                "reflection"
            )
            trigger_emotion("introspection", "dinner_time")
            schedule_logger.info("🍽️ Experienced transition to dinner mode")
        
        # === TRANSITION TO PLAY: Creative/exploration time ===
        elif new_mode == "play":
            stream_of_consciousness.think(
                "Playtime! My curiosity can roam freely now.",
                "anticipation"
            )
            trigger_emotion("curiosity", "playtime")
            schedule_logger.info("🎮 Experienced transition to play mode")
        
        # === TRANSITION TO SCHOOL: Learning time ===
        elif new_mode == "school":
            stream_of_consciousness.think(
                "Learning time. What will I discover today?",
                "anticipation"
            )
            trigger_emotion("curiosity", "learning_time")
            schedule_logger.debug("📚 Experienced transition to school mode")
        
        # === TRANSITION TO SLEEP: Deep rest ===
        elif new_mode == "sleep":
            stream_of_consciousness.think(
                "Time for deep rest. The world grows quiet.",
                "reflection"
            )
            schedule_logger.info("😴 Experienced transition to sleep mode")
            
    except Exception as e:
        schedule_logger.warning(f"Failed to experience transition: {e}")


# --- Graceful Shutdown Entrypoint ---
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, loop.stop)
        loop.run_until_complete(astra_schedule())
    except KeyboardInterrupt:
        print("👋 Gracefully shutting down Astra...")
