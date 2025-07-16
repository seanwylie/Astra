# beta/utils/__init__.py

"""
🛠️ Beta Utils Module
--------------------
Utility functions and helpers for the Astra beta implementation.

This module provides common utilities used across the beta system,
including Discord helpers, text processing, and shared functions.

Author: Sean Wylie
Created: 2025-01-16
"""

# Discord utilities
from .discord_helpers import *
from .send_chunked_message import send_chunked_message

# Common utilities
from .common_utils import (
    chunk_text,
    clean_text,
    is_similar_text,
    extract_keywords,
    validate_config,
    safe_get,
    safe_load_json,
    safe_save_json,
    format_timestamp,
    format_duration,
    truncate_text,
    safe_execute,
    iso_now,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_SIMILARITY_THRESHOLD,
    COMMON_BREAK_POINTS
)

# Utility categories
TEXT_UTILS = [
    'chunk_text',
    'clean_text', 
    'is_similar_text',
    'extract_keywords',
    'truncate_text'
]

DATA_UTILS = [
    'validate_config',
    'safe_get',
    'safe_load_json',
    'safe_save_json'
]

FORMAT_UTILS = [
    'format_timestamp',
    'format_duration',
    'iso_now'
]

DISCORD_UTILS = [
    'send_chunked_message'
]

ERROR_UTILS = [
    'safe_execute'
]

ALL_UTILS = TEXT_UTILS + DATA_UTILS + FORMAT_UTILS + DISCORD_UTILS + ERROR_UTILS

__all__ = ALL_UTILS + [
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_SIMILARITY_THRESHOLD', 
    'COMMON_BREAK_POINTS'
]