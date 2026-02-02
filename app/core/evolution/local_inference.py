"""
Astra Evolution: Local model inference with corpus-as-context.

When OLLAMA_BASE_URL (and optionally OLLAMA_MODEL) are set, provides
a reflection/response using a local model (e.g. Ollama) with a slice
of the Astra corpus as context. No training yet; context injection only.
"""

import os
from typing import Any, Dict, List, Optional

# Optional: use requests if available for sync, or fall back to urllib
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


def _get_config() -> Dict[str, Any]:
    """Base URL and model for local inference. Env overrides."""
    base = os.getenv("OLLAMA_BASE_URL", "").strip() or os.getenv("LOCAL_MODEL_URL", "").strip()
    model = os.getenv("OLLAMA_MODEL", "llama3.2").strip()
    try:
        from app.config.loader import load_config
        cfg = load_config("general_config") or {}
        if not base:
            base = (cfg.get("local_model_base_url") or "").strip()
        if not model:
            model = (cfg.get("local_model_name") or "llama3.2").strip()
    except Exception:
        pass
    return {"base_url": base.rstrip("/"), "model": model or "llama3.2"}


def is_local_inference_available() -> bool:
    """True if a local model base URL is configured."""
    return bool(_get_config().get("base_url"))


def _corpus_context_block(entries: List[Dict[str, Any]], max_chars: int = 4000) -> str:
    """Format corpus entries as a single context string."""
    parts = []
    n = 0
    for e in entries:
        role = e.get("role", "text")
        content = (e.get("content") or "").strip()
        if not content:
            continue
        line = f"[{role}] {content[:500]}"
        if n + len(line) > max_chars:
            break
        parts.append(line)
        n += len(line)
    return "\n".join(parts) if parts else ""


def query_local_model(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    corpus_max_lines: int = 300,
    max_tokens: int = 150,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Call local model (Ollama-compatible API) with corpus slice as context.
    Returns generated text or None if disabled/failed.
    """
    cfg = _get_config()
    base_url = cfg.get("base_url")
    if not base_url:
        return None

    if not _HAS_REQUESTS:
        return None

    try:
        from app.core.evolution.corpus_export import load_corpus_slice
        entries = load_corpus_slice(max_lines=corpus_max_lines)
    except Exception:
        entries = []

    context_block = _corpus_context_block(entries)
    if context_block:
        full_prompt = f"Relevant context from Astra's mind:\n{context_block}\n\n---\n\n{user_prompt}"
    else:
        full_prompt = user_prompt

    # Ollama /api/generate (completion) or /api/chat
    url = f"{base_url}/api/generate"
    payload = {
        "model": cfg.get("model", "llama3.2"),
        "prompt": full_prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    if system_prompt:
        # Some setups use /api/chat with messages
        url_chat = f"{base_url}/api/chat"
        payload_chat = {
            "model": cfg.get("model", "llama3.2"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        try:
            r = requests.post(url_chat, json=payload_chat, timeout=60)
            r.raise_for_status()
            data = r.json()
            msg = (data.get("message") or {})
            text = (msg.get("content") or "").strip()
            return text or None
        except Exception:
            pass

    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
        return text or None
    except Exception:
        return None


async def query_local_model_async(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    corpus_max_lines: int = 300,
    max_tokens: int = 150,
    temperature: float = 0.7,
) -> Optional[str]:
    """Async wrapper: run query_local_model in executor to avoid blocking."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: query_local_model(
            user_prompt,
            system_prompt=system_prompt,
            corpus_max_lines=corpus_max_lines,
            max_tokens=max_tokens,
            temperature=temperature,
        ),
    )
