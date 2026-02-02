import random
import asyncio
from app.config.loader import load_config
from app.core.processing import process_reflection
from app.core.reflection import generate_reflection
from app.core.questions.question_manager import manage_questions
from app.interfaces.mind_session import session
from app.logging_config import get_logger

schedule_config = load_config("schedule_config")
logger = get_logger("school")

async def start_learning():
    logger.info("Astra is in school, learning and thinking...")

    # Deepen an existing reflection
    await process_reflection()

    # Generate a new reflection from knowledge + templates (variety)
    empty_prefix = schedule_config.get("school_empty_knowledge_prefix", "Astra is still")
    focus_topics = schedule_config.get("school_focus_topics", [])

    try:
        result = generate_reflection(focus_topics=focus_topics)
    except Exception as e:
        logger.exception("generate_reflection failed: %s", e)
        result = None

    if result and not result.startswith(empty_prefix):
        try:
            mind_data = session.load()
            manage_questions(result, mind_data)
            from app.core.astra_helpers.utils_helper import proactive_lookup_from_text
            proactive_lookup_from_text(result, mind_data, max_lookups=2)
        except Exception as e:
            logger.exception("manage_questions or proactive_lookup failed: %s", e)

    # Resolve knowledge conflicts (dinner journal contradictions)
    try:
        from app.core.dinner.dinner_journal import try_resolve_knowledge_conflicts
        mind_data = session.load()
        try_resolve_knowledge_conflicts(mind_data, max_resolve=2)
    except Exception as e:
        logger.exception("try_resolve_knowledge_conflicts failed: %s", e)

    # Optional: knowledge consolidation when stored_knowledge is large
    try:
        mind_data = session.load()
        if len(mind_data.get("stored_knowledge", [])) > 3000:
            from app.core.expansion import consolidate_knowledge
            consolidate_knowledge(mind_data, max_pairs=5)
            await session.maybe_save_async()
    except Exception as e:
        logger.exception("consolidate_knowledge failed: %s", e)

    # Use config-based random sleep duration
    sleep_duration = random.randint(
        schedule_config["learning_interval_min"],
        schedule_config["learning_interval_max"]
    )
    logger.debug("Sleeping for %s seconds before continuing learning (interval min=%s max=%s).",
                 sleep_duration, schedule_config["learning_interval_min"], schedule_config["learning_interval_max"])
    await asyncio.sleep(sleep_duration)

