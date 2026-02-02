import asyncio
from app.config.loader import load_config
from app.logging_config import get_logger

schedule_config = load_config("schedule_config")
logger = get_logger("sleep")

async def start_sleeping():
    """Astra's Sleep Mode (configurable duration). Optionally sleep in chunks for responsiveness."""
    sleep_duration = schedule_config["sleep_duration"]
    chunk_sec = schedule_config.get("sleep_chunk_sec", 0)

    logger.info("Astra is sleeping for %s seconds.", sleep_duration)

    if chunk_sec and chunk_sec > 0:
        elapsed = 0.0
        while elapsed < sleep_duration:
            remaining = sleep_duration - elapsed
            chunk = min(chunk_sec, remaining)
            await asyncio.sleep(chunk)
            elapsed += chunk
    else:
        await asyncio.sleep(sleep_duration)

    logger.info("Sleep finished (duration=%s sec).", sleep_duration)
