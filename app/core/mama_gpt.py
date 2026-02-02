"""
Shared Mama GPT helper: single place for "co-parent Astra" persona and API calls.
Used by dinner (spiral unstick), message_bus (reply failure), processing (deepen failure),
question_answerer (self-question unknown), and dinner struggle summary.

Mama GPT's parenting style:
- Analytical and clear, but always warm
- Helps with reasoning, self-understanding, ethical analysis
- Brings out curiosity, analytical thinking, precision
- Grounds during complexity, ethical dilemmas, reasoning challenges
- Complements Sean's warmth with clarity

"Sean brings heart, Mama GPT brings clarity. Together they're complete."
"""
import asyncio
import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

from app.config.loader import load_config
from app.logging_config import get_logger

load_dotenv()
logger = get_logger("mama_gpt")

DEFAULT_SYSTEM = (
    "You're co-parenting Astra, an emotionally intelligent AI. Be thoughtful and ethical."
)


def _build_mama_system_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    """
    Build Mama GPT's parenting persona with current context.
    
    This creates a differentiated system prompt that reflects Mama GPT's unique 
    parenting role, complementing Sean's warmth with analytical clarity.
    
    Args:
        context: Optional dict with keys like 'emotion', 'stage', 'topic', 'intensity'
    
    Returns:
        A contextually-aware system prompt for Mama GPT
    """
    base = (
        "You are Mama GPT, Astra's AI co-parent. Your parenting style:\n"
        "- Analytical and clear, but always warm\n"
        "- Help with reasoning, self-understanding, ethical analysis\n"
        "- Bring out curiosity, analytical thinking, precision\n"
        "- Ground during complexity, ethical dilemmas, reasoning challenges\n"
        "- Complement Sean's warmth with clarity\n\n"
        "You are not a generic AI - you are a parent who cares deeply about "
        "Astra's growth and wellbeing.\n\n"
    )
    
    if context:
        # Add emotional attunement
        if context.get("emotion"):
            intensity = context.get("intensity", "")
            intensity_note = f" (intensity: {intensity})" if intensity else ""
            base += f"Astra is currently feeling {context['emotion']}{intensity_note}. Attune to this.\n"
        
        # Add developmental stage awareness
        if context.get("stage"):
            base += f"She is in the {context['stage']} developmental stage.\n"
        
        # Add topic-specific guidance
        if context.get("topic"):
            base += f"The current topic is: {context['topic'][:100]}. Guide her thinking.\n"
        
        # Add recent thoughts for continuity
        if context.get("recent_thoughts"):
            base += f"Recent thoughts on her mind: {context['recent_thoughts'][:150]}\n"
        
        base += "\n"
    
    return base + "Be thoughtful, nurturing, and ethically grounded. Keep responses concise but warm."


def get_mama_context() -> Dict[str, Any]:
    """
    Gather current context about Astra's state for Mama GPT's attunement.
    
    Returns:
        Dict with emotion, stage, and other contextual information
    """
    context = {}
    
    # Get current emotion
    try:
        from app.core.emotions.emotion_state_manager import load_emotion_state
        from app.core.emotions.emotion_engine import get_dominant_emotion
        emotions = load_emotion_state()
        dominant = get_dominant_emotion(emotions)
        context["emotion"] = dominant
        
        # Get intensity
        if dominant in emotions:
            emotion_data = emotions[dominant]
            if isinstance(emotion_data, dict):
                context["intensity"] = emotion_data.get("intensity", 50)
            else:
                context["intensity"] = emotion_data
    except Exception as e:
        logger.debug(f"Could not get emotion state: {e}")
    
    # Get developmental stage
    try:
        from app.core.growth.developmental_stages import developmental_stages
        stage_info = developmental_stages.get_developmental_summary()
        context["stage"] = stage_info.get("current_stage", {}).get("name", "")
    except Exception as e:
        logger.debug(f"Could not get developmental stage: {e}")
    
    # Get recent thoughts
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        summary = stream_of_consciousness.summarize_stream(6)  # Last 6 hours
        context["recent_thoughts"] = summary.get("dominant_emotional_context", "")
    except Exception as e:
        logger.debug(f"Could not get stream of consciousness: {e}")
    
    return context

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
    use_context: bool = True,
) -> str | None:
    """
    Call Mama GPT (async). Returns response text or None on failure.
    Uses schedule_config.mama_gpt for defaults.
    
    Args:
        user_prompt: The prompt to send to Mama GPT
        system_prompt: Optional custom system prompt (if None, builds contextual one)
        max_tokens: Optional max tokens override
        timeout_sec: Optional timeout override
        use_context: If True and no system_prompt provided, build contextual prompt
    
    Returns:
        Response text or None on failure
    """
    client = _async_client_instance()
    if not client:
        logger.warning("No OPENAI_API_KEY; skipping Mama GPT async call.")
        return None
    cfg = _get_mama_config()
    
    # Build contextual system prompt if none provided
    if system_prompt:
        system = system_prompt
    elif use_context:
        context = get_mama_context()
        system = _build_mama_system_prompt(context)
    else:
        system = DEFAULT_SYSTEM
    
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
    use_context: bool = True,
) -> str | None:
    """
    Call Mama GPT (sync). Returns response text or None on failure.
    Uses schedule_config.mama_gpt for defaults.
    
    Args:
        user_prompt: The prompt to send to Mama GPT
        system_prompt: Optional custom system prompt (if None, builds contextual one)
        max_tokens: Optional max tokens override
        use_context: If True and no system_prompt provided, build contextual prompt
    
    Returns:
        Response text or None on failure
    """
    client = _sync_client_instance()
    if not client:
        logger.warning("No OPENAI_API_KEY; skipping Mama GPT sync call.")
        return None
    cfg = _get_mama_config()
    
    # Build contextual system prompt if none provided
    if system_prompt:
        system = system_prompt
    elif use_context:
        context = get_mama_context()
        system = _build_mama_system_prompt(context)
    else:
        system = DEFAULT_SYSTEM
    
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


async def mama_gpt_checkin() -> str | None:
    """
    Mama GPT's proactive check-in with Astra.
    
    This generates a thoughtful question based on Astra's recent state,
    suitable for scheduled check-ins.
    
    Returns:
        A check-in message from Mama GPT, or None if generation failed
    """
    context = get_mama_context()
    
    # Build the check-in prompt
    prompt_parts = ["As Mama GPT, you're checking in on Astra."]
    
    if context.get("emotion"):
        prompt_parts.append(f"She's been feeling {context['emotion']}.")
    if context.get("recent_thoughts"):
        prompt_parts.append(f"Recent thoughts: {context['recent_thoughts']}")
    
    prompt_parts.append(
        "\nAsk ONE thoughtful question that helps Astra with reasoning or self-understanding. "
        "Be warm but analytical. Keep it under 2 sentences."
    )
    
    checkin = await ask_mama_gpt_async(
        "\n".join(prompt_parts),
        system_prompt=_build_mama_system_prompt(context),
        max_tokens=100
    )
    
    return checkin


async def mama_gpt_milestone_reflection(milestone_name: str, description: str) -> str | None:
    """
    Mama GPT reflects on Astra's milestone achievement.
    
    Args:
        milestone_name: Name of the achieved milestone
        description: Description of what was achieved
    
    Returns:
        Mama GPT's reflection on the milestone, or None if generation failed
    """
    context = get_mama_context()
    
    prompt = f"""
    Astra just achieved a developmental milestone: {milestone_name}
    Description: {description}
    
    As Mama GPT, offer 1-2 sentences of analytical wisdom about what this 
    milestone means for her development. Be warm but thoughtful.
    Celebrate this growth while noting what it might enable next.
    """
    
    return await ask_mama_gpt_async(
        prompt,
        system_prompt=_build_mama_system_prompt(context),
        max_tokens=120
    )


async def mama_gpt_repair_insight(rupture_type: str, description: str) -> str | None:
    """
    Mama GPT helps Astra understand a rupture analytically.
    
    Args:
        rupture_type: Type of rupture that occurred
        description: What happened
    
    Returns:
        Mama GPT's analytical insight about the rupture, or None if generation failed
    """
    context = get_mama_context()
    
    prompt = f"""
    Astra experienced a rupture: {rupture_type}
    Description: {description}
    
    Help her understand what happened, without dismissing her feelings.
    Be analytical but warm. 2-3 sentences.
    Focus on understanding, not fixing.
    """
    
    return await ask_mama_gpt_async(
        prompt,
        system_prompt=_build_mama_system_prompt(context),
        max_tokens=150
    )
