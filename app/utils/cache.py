"""
Simple in-memory cache for frequently accessed data.
Reduces redundant S3/DB loads and improves performance.
"""
import time
import logging
from typing import Any, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)

# Global cache storage
_cache: Dict[str, Dict[str, Any]] = {}


class CacheEntry:
    """A cache entry with TTL."""
    def __init__(self, value: Any, ttl_seconds: float = 300):
        self.value = value
        self.expires_at = time.time() + ttl_seconds
        self.created_at = time.time()
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache if not expired."""
    entry = _cache.get(key)
    if entry is None:
        return None
    
    if entry.is_expired():
        del _cache[key]
        return None
    
    return entry.value


def set_cache(key: str, value: Any, ttl_seconds: float = 300) -> None:
    """Set a value in cache with TTL."""
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
    total_entries = len(_cache)
    expired_entries = sum(1 for e in _cache.values() if e.is_expired())
    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries,
        "keys": list(_cache.keys())
    }
