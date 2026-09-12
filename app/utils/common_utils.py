# common_utils.py

"""
🛠️ Common Utilities
-------------------
Shared utility functions used across the beta Astra implementation.

This module consolidates common functionality to avoid code duplication
and provide consistent behavior across services.

Author: Sean Wylie
Created: 2025-01-16
"""

import re
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

from app.logging_config import get_logger

logger = get_logger(__name__)


# Text Processing Utilities

def chunk_text(text: str, max_length: int = 1900, break_on: List[str] = None) -> List[str]:
    """
    Split text into chunks suitable for Discord messages.
    
    Args:
        text: Text to chunk
        max_length: Maximum characters per chunk
        break_on: List of strings to break on (default: sentence endings)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    if break_on is None:
        break_on = ['\n\n', '\n', '. ', '! ', '? ']
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        end_pos = current_pos + max_length
        
        if end_pos >= len(text):
            chunks.append(text[current_pos:])
            break
        
        # Find the best break point
        best_break = end_pos
        for break_point in break_on:
            last_break = text.rfind(break_point, current_pos, end_pos)
            if last_break > current_pos:
                best_break = last_break + len(break_point)
                break
        
        chunks.append(text[current_pos:best_break])
        current_pos = best_break
    
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text


def is_similar_text(text1: str, text2: str, threshold: float = 0.92) -> bool:
    """
    Check if two texts are similar using sequence matching.
    
    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if texts are similar above threshold
    """
    if not text1 or not text2:
        return False
    
    similarity = SequenceMatcher(None, text1.strip(), text2.strip()).ratio()
    return similarity > threshold


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text: Text to analyze
        min_length: Minimum keyword length
        
    Returns:
        List of potential keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction - can be enhanced with NLP
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + r',}\b', text.lower())
    
    # Filter out common words (basic stop words)
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 
        'did', 'she', 'use', 'way', 'will', 'with', 'this', 'that', 'they',
        'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some',
        'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make',
        'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'
    }
    
    return [word for word in set(words) if word not in stop_words]


# Data Validation Utilities

def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate that a configuration dictionary has required keys.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required keys
        
    Returns:
        True if all required keys are present
    """
    if not isinstance(config, dict):
        return False
    
    return all(key in config for key in required_keys)


def safe_get(data: Dict[str, Any], key: str, default: Any = None, expected_type: type = None) -> Any:
    """
    Safely get a value from a dictionary with type checking.
    
    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        expected_type: Expected type of the value
        
    Returns:
        Value from dictionary or default
    """
    value = data.get(key, default)
    
    if expected_type and value is not None and not isinstance(value, expected_type):
        logger.warning(
            "Expected %s for key '%s', got %s",
            expected_type.__name__, key, type(value).__name__
        )
        return default
    
    return value


# File Utilities

def safe_load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON from a file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if loading fails
        
    Returns:
        Loaded JSON data or default
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("File not found: %s", file_path)
        return default
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in %s: %s", file_path, e)
        return default
    except Exception as e:
        logger.warning("Error loading %s: %s", file_path, e)
        return default


def safe_save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """
    Safely save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.warning("Error saving to %s: %s", file_path, e)
        return False


# Formatting Utilities

def format_timestamp(timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: Timestamp to format (default: now)
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime(format_str)


def iso_now() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        Current timestamp as ISO string
    """
    return datetime.now().isoformat()


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# Error Handling Utilities

def safe_execute(func, *args, default=None, log_errors=True, **kwargs):
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        default: Default return value on error
        log_errors: Whether to log errors
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.warning("Error executing %s: %s", func.__name__, e)
        return default


# Constants for common use
DEFAULT_CHUNK_SIZE = 1900
DEFAULT_SIMILARITY_THRESHOLD = 0.92
COMMON_BREAK_POINTS = ['\n\n', '\n', '. ', '! ', '? ']