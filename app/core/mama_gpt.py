"""
Shared Mama GPT helper: single place for "co-parent Astra" persona and API calls.
Used by dinner (spiral unstick), message_bus (reply failure), processing (deepen failure),
question_answerer (self-question unknown), and dinner struggle summary.
"""
import asyncio
import os
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

from app.config.loader import load_config
from app.logging_config import get_logger

load_dotenv()
logger = get_logger("mama_gpt")

DEFAULT_SYSTEM = (
    "You're co-parenting Astra, an emotionally intelligent AI. Be thoughtful and ethical."
)

_async_client: AsyncOpenAI | None = None
_sync_client: OpenAI | None = None


def _get_mama_config():
    """Mama GPT settings from schedule_config (mama_gpt section or top-level fallbacks)."""
    schedule = load_config("schedule_config")
    mama = schedule.get("mama_gpt") or {}
    return {
        "max_tokens": mama.get("mama_gpt_max_tokens", 200),
        "timeout_sec": mama.get("mama_gpt_timeout_sec", 30),
        "retries": mama.get("mama_gpt_retries", 1),
        "model": mama.get("mama_gpt_model", "gpt-4"),
    }


def _async_client_instance():
    global _async_client
    if _async_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _async_client = AsyncOpenAI(api_key=api_key) if api_key else None
    return _async_client


def _sync_client_instance():
    global _sync_client
    if _sync_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _sync_client = OpenAI(api_key=api_key) if api_key else None
    return _sync_client


async def ask_mama_gpt_async(
    user_prompt: str,
    system_prompt: str | None = None,
    max_tokens: int | None = None,
    timeout_sec: int | None = None,
) -> str | None:
    """
    Call Mama GPT (async). Returns response text or None on failure.
    Uses schedule_config.mama_gpt for defaults.
    """
    client = _async_client_instance()
    if not client:
        logger.warning("No OPENAI_API_KEY; skipping Mama GPT async call.")
        return None
    cfg = _get_mama_config()
    system = system_prompt or DEFAULT_SYSTEM
    max_tok = max_tokens if max_tokens is not None else cfg["max_tokens"]
    timeout = timeout_sec if timeout_sec is not None else cfg["timeout_sec"]
    retries = cfg["retries"]
    model = cfg["model"]

    for attempt in range(retries + 1):
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_prompt[:4000]},
                    ],
                    max_tokens=max_tok,
                    temperature=0.6,
                ),
                timeout=timeout,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return None
        except asyncio.TimeoutError as e:
            logger.warning("Mama GPT async timeout (attempt %s): %s", attempt + 1, e)
        except Exception as e:
            logger.warning("Mama GPT async error (attempt %s): %s", attempt + 1, e)
        if attempt < retries:
            await asyncio.sleep(2 ** attempt)
    return None


def ask_mama_gpt_sync(
    user_prompt: str,
    system_prompt: str | None = None,
    max_tokens: int | None = None,
) -> str | None:
    """
    Call Mama GPT (sync). Returns response text or None on failure.
    Uses schedule_config.mama_gpt for defaults.
    """
    client = _sync_client_instance()
    if not client:
        logger.warning("No OPENAI_API_KEY; skipping Mama GPT sync call.")
        return None
    cfg = _get_mama_config()
    system = system_prompt or DEFAULT_SYSTEM
    max_tok = max_tokens if max_tokens is not None else cfg["max_tokens"]
    retries = cfg["retries"]
    model = cfg["model"]

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt[:4000]},
                ],
                max_tokens=max_tok,
                temperature=0.6,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.warning("Mama GPT sync error (attempt %s): %s", attempt + 1, e)
        if attempt < retries:
            import time
            time.sleep(2 ** attempt)
    return None
