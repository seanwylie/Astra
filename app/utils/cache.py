"""
Simple in-memory cache for frequently accessed data.
Reduces redundant S3/DB loads and improves performance.
"""
import time
import logging
from typing import Any, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """A cache entry with TTL."""
    def __init__(self, value: Any, ttl_seconds: float = 300):
        self.value = value
        self.expires_at = time.time() + ttl_seconds
        self.created_at = time.time()
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


# Global cache storage
# MEMORY LEAK FIX: Add size limit to prevent unbounded growth
_cache: Dict[str, CacheEntry] = {}
_MAX_CACHE_ENTRIES = 100  # Hard limit to prevent memory leak


def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache if not expired."""
    entry = _cache.get(key)
    if entry is None:
        return None
    
    if entry.is_expired():
        del _cache[key]
        return None
    
    return entry.value


def _cleanup_expired_cache():
    """Remove expired entries from cache."""
    expired_keys = [k for k, v in _cache.items() if v.is_expired()]
    for key in expired_keys:
        del _cache[key]
    return len(expired_keys)


def _enforce_cache_limit():
    """Enforce cache size limit by removing oldest entries."""
    if len(_cache) <= _MAX_CACHE_ENTRIES:
        return
    
    # Sort by creation time and remove oldest
    sorted_entries = sorted(_cache.items(), key=lambda x: x[1].created_at)
    to_remove = len(_cache) - _MAX_CACHE_ENTRIES
    for key, _ in sorted_entries[:to_remove]:
        del _cache[key]
    logger.warning("Cache exceeded limit (%s entries), removed %s oldest entries", len(_cache) + to_remove, to_remove)


def set_cache(key: str, value: Any, ttl_seconds: float = 300) -> None:
    """Set a value in cache with TTL."""
    # MEMORY LEAK FIX: Clean up expired entries and enforce limit before adding
    _cleanup_expired_cache()
    _enforce_cache_limit()
    
    _cache[key] = CacheEntry(value, ttl_seconds)
    logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")


def clear_cache(key: Optional[str] = None) -> None:
    """Clear cache entry or all cache if key is None."""
    if key is None:
        _cache.clear()
        logger.debug("Cache cleared")
    elif key in _cache:
        del _cache[key]
        logger.debug(f"Cache cleared: {key}")


def cache_result(ttl_seconds: float = 300, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = get_cache(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Call function and cache result
            result = func(*args, **kwargs)
            set_cache(cache_key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    # Clean expired entries first
    _cleanup_expired_cache()
    total_entries = len(_cache)
    expired_entries = sum(1 for e in _cache.values() if e.is_expired())
    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries,
        "keys": list(_cache.keys())
    }


def periodic_cache_cleanup():
    """Periodic cleanup of expired cache entries. Call this periodically."""
    cleaned = _cleanup_expired_cache()
    if cleaned > 0:
        logger.debug(f"Cleaned {cleaned} expired cache entries")
    _enforce_cache_limit()
