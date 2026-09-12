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

try:
    from app.logging_config import get_logger
    logger = get_logger("local_inference")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

_last_error: Optional[Exception] = None  # set when query_local_model fails (for diagnostics)

# Junk/code tokens to filter from corpus context (and to validate output); keep in sync with processing.is_valid_reflection
_CORPUS_JUNK_TOKENS = frozenset([
    "strokelength", "strokeline", "initcomponents", "getelementbyid",
    "addeventlistener", "innerhtml", "createelement", "queryselector",
])


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


def _is_local_inference_disabled_for_scope(scope: Optional[str]) -> bool:
    """True if local inference is disabled globally or for the given scope."""
    if os.getenv("OLLAMA_DISABLED", "").strip().lower() in ("1", "true", "yes"):
        return True
    if not scope:
        return False
    scope_upper = scope.upper().replace("-", "_")
    env_name = f"OLLAMA_DISABLE_FOR_{scope_upper}"
    if os.getenv(env_name, "").strip().lower() in ("1", "true", "yes"):
        return True
    try:
        from app.config.loader import load_config
        cfg = load_config("general_config") or {}
        disabled_list = cfg.get("local_inference_disabled_for") or []
        if isinstance(disabled_list, list) and scope in disabled_list:
            return True
    except Exception:
        pass
    return False


def is_local_inference_available(scope: Optional[str] = None) -> bool:
    """True if a local model base URL is configured and not disabled for scope.
    scope: optional 'school' or 'dream' to check per-feature disable flags."""
    if _is_local_inference_disabled_for_scope(scope):
        return False
    return bool(_get_config().get("base_url"))


def get_last_inference_error() -> Optional[Exception]:
    """Return the last exception from query_local_model, if any (for diagnostics)."""
    return _last_error


def _corpus_context_block(entries: List[Dict[str, Any]], max_chars: int = 4000) -> str:
    """Format corpus entries as a single context string. Skips entries that look like code/junk."""
    parts = []
    n = 0
    for e in entries:
        role = e.get("role", "text")
        content = (e.get("content") or "").strip()
        if not content:
            continue
        content_lower = content.lower()
        if any(token in content_lower for token in _CORPUS_JUNK_TOKENS):
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
    global _last_error
    _last_error = None
    cfg = _get_config()
    base_url = cfg.get("base_url")
    if not base_url:
        return None

    if not _HAS_REQUESTS:
        return None

    try:
        from app.core.evolution.corpus_export import load_corpus_slice
        entries = load_corpus_slice(max_lines=corpus_max_lines)
        logger.debug("[query_local_model] Loaded %s corpus entries", len(entries))
    except Exception as e:
        logger.debug("[query_local_model] Failed to load corpus: %s", e)
        entries = []

    context_block = _corpus_context_block(entries)
    if context_block:
        full_prompt = f"Relevant context from Astra's mind:\n{context_block}\n\n---\n\n{user_prompt}"
        logger.debug("[query_local_model] Using corpus context (%s chars)", len(context_block))
    else:
        full_prompt = user_prompt
        logger.debug("[query_local_model] No corpus context available")

    model_name = cfg.get("model", "llama3.2")
    logger.debug("[query_local_model] Calling Ollama model '%s' at %s", model_name, base_url)

    # Ollama /api/generate (completion) or /api/chat
    url = f"{base_url}/api/generate"
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    
    if system_prompt:
        # Some setups use /api/chat with messages
        url_chat = f"{base_url}/api/chat"
        payload_chat = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        try:
            logger.debug("[query_local_model] Trying /api/chat endpoint")
            r = requests.post(url_chat, json=payload_chat, timeout=60)
            r.raise_for_status()
            data = r.json()
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.warning("[query_local_model] /api/chat returned non-dict response: %s", type(data))
                raise ValueError(f"Invalid response type: {type(data)}")
            
            # Check for error in response
            if "error" in data:
                error_msg = data.get("error", "Unknown error")
                logger.warning("[query_local_model] Ollama /api/chat error: %s", error_msg)
                _last_error = Exception(f"Ollama API error: {error_msg}")
                raise _last_error
            
            msg = data.get("message")
            if not isinstance(msg, dict):
                logger.warning("[query_local_model] /api/chat response missing 'message' dict. Response keys: %s", list(data.keys()))
                logger.debug("[query_local_model] Full response: %s", str(data)[:500])
                raise ValueError("Response missing 'message' field")
            
            text = msg.get("content", "")
            if not isinstance(text, str):
                logger.warning("[query_local_model] /api/chat 'content' is not a string: %s", type(text))
                raise ValueError(f"Content is not a string: {type(text)}")
            
            text = text.strip()
            logger.debug("[query_local_model] /api/chat returned %s chars: %s", len(text), text[:100])
            
            if not text:
                logger.debug("[query_local_model] /api/chat returned empty content")
                return None

            from app.core.processing import is_valid_reflection
            if not is_valid_reflection(text):
                logger.warning(
                    "[query_local_model] Local model output rejected (quality check failed): %.80s...",
                    text[:80] if len(text) > 80 else text,
                )
                _last_error = ValueError("Local model output failed validation")
                return None
            
            return text
            
        except requests.exceptions.Timeout:
            logger.warning("[query_local_model] Ollama /api/chat timeout after 60s")
            _last_error = Exception("Ollama API timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("[query_local_model] Ollama /api/chat request failed: %s", e)
            _last_error = e
            # Fall through to /api/generate
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("[query_local_model] Ollama /api/chat response parsing failed: %s", e)
            logger.debug("[query_local_model] Response data: %s", str(data)[:500] if 'data' in locals() else "N/A")
            _last_error = e
            # Fall through to /api/generate
        except Exception as e:
            logger.warning("[query_local_model] Ollama /api/chat unexpected error: %s", e, exc_info=True)
            _last_error = e
            # Fall through to /api/generate

    # Fallback to /api/generate
    try:
        logger.debug("[query_local_model] Trying /api/generate endpoint")
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        
        # Validate response structure
        if not isinstance(data, dict):
            logger.warning("[query_local_model] /api/generate returned non-dict response: %s", type(data))
            raise ValueError(f"Invalid response type: {type(data)}")
        
        # Check for error in response
        if "error" in data:
            error_msg = data.get("error", "Unknown error")
            logger.warning("[query_local_model] Ollama /api/generate error: %s", error_msg)
            _last_error = Exception(f"Ollama API error: {error_msg}")
            raise _last_error
        
        text = data.get("response", "")
        if not isinstance(text, str):
            logger.warning("[query_local_model] /api/generate 'response' is not a string: %s", type(text))
            logger.debug("[query_local_model] Response keys: %s", list(data.keys()))
            raise ValueError(f"Response is not a string: {type(text)}")
        
        text = text.strip()
        logger.debug("[query_local_model] /api/generate returned %s chars: %s", len(text), text[:100])
        
        if not text:
            logger.debug("[query_local_model] /api/generate returned empty response")
            return None

        from app.core.processing import is_valid_reflection
        if not is_valid_reflection(text):
            logger.warning(
                "[query_local_model] Local model output rejected (quality check failed): %.80s...",
                text[:80] if len(text) > 80 else text,
            )
            _last_error = ValueError("Local model output failed validation")
            return None
        
        return text
        
    except requests.exceptions.Timeout:
        logger.warning("[query_local_model] Ollama /api/generate timeout after 60s")
        _last_error = Exception("Ollama API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("[query_local_model] Ollama /api/generate request failed: %s", e)
        _last_error = e
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.warning("[query_local_model] Ollama /api/generate response parsing failed: %s", e)
        logger.debug("[query_local_model] Response data: %s", str(data)[:500] if 'data' in locals() else "N/A")
        _last_error = e
        return None
    except Exception as e:
        logger.warning("[query_local_model] Ollama /api/generate unexpected error: %s", e, exc_info=True)
        _last_error = e
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
