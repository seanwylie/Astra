"""
Unified configuration loader for Astra.
Single source of truth: config files live in project root config/.
No global print override; use logging in callers.
"""
import json
import os
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root = parent of app/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = Path(os.getenv("ASTRA_CONFIG_DIR", str(_PROJECT_ROOT / "config")))

if not CONFIG_DIR.is_dir():
    logger.warning("Config directory not found: %s", CONFIG_DIR)

_CONFIG_CACHE: dict[str, dict[str, Any]] = {}

_VALIDATION_RULES: dict[str, list[str]] = {
    "discord_config.json": ["discord_channel"],
    "values_config.json": ["values"],
    "strings_config.json": ["responses", "emojis"],
    "general_config.json": ["reflection_interval", "question_templates", "deeper_thought_templates"],
    "schedule_config.json": ["timezone", "dream_time", "learning_time", "state_change_messages"],
    "emotion_config.json": ["emotions", "max_intensity"],
    "mood_config.json": ["moods", "mood_influences"],
    "config_soul.json": ["soul"],
}


def load_config(filename: str) -> dict[str, Any]:
    """Load a JSON config file with caching. Uses project config/ directory."""
    if not filename.endswith(".json"):
        filename += ".json"

    if filename in _CONFIG_CACHE:
        return _CONFIG_CACHE[filename]

    file_path = CONFIG_DIR / filename
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not _validate_config(filename, data):
            logger.warning("Config validation failed for %s", filename)
            data = {}
        _apply_env_overrides(filename, data)
        _CONFIG_CACHE[filename] = data
        return data
    except FileNotFoundError:
        logger.warning("Config file not found: %s", file_path)
        _CONFIG_CACHE[filename] = {}
        return {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", file_path, e)
        _CONFIG_CACHE[filename] = {}
        return {}


def _validate_config(config_name: str, config: dict[str, Any]) -> bool:
    required = _VALIDATION_RULES.get(config_name, [])
    for key in required:
        if key not in config:
            logger.error("Missing required key '%s' in %s", key, config_name)
            return False
    return True


# Env vars override these config keys when set (so one repo works across environments)
_ENV_OVERRIDES: dict[str, dict[str, str]] = {
    "discord_config.json": {
        "discord_channel": "DISCORD_CHANNEL_ID",
        "mind_file_path": "ASTRA_MIND_FILE",
        "mind_file_sean_path": "ASTRA_MIND_FILE_SEAN",
        "log_file": "ASTRA_LOG_FILE",
    },
    "general_config.json": {
        "mind_file_path": "ASTRA_MIND_FILE",
        "mind_file_sean_path": "ASTRA_MIND_FILE_SEAN",
        "log_file": "ASTRA_LOG_FILE",
    },
}


def _apply_env_overrides(config_name: str, data: dict[str, Any]) -> None:
    """Overlay env vars onto config so paths and channel ID can be set per environment."""
    overrides = _ENV_OVERRIDES.get(config_name, {})
    for config_key, env_key in overrides.items():
        value = os.getenv(env_key)
        if value is not None and value.strip():
            data[config_key] = value.strip()


def get_config(key: str, default: Any = None, config_file: str = "general_config") -> Any:
    """Get a key from a config file with env fallback."""
    if not config_file.endswith(".json"):
        config_file += ".json"
    data = load_config(config_file)
    return data.get(key, os.getenv(key.upper(), default))


class ConfigManager:
    """Convenience manager for Discord/values config (backward compatible)."""

    def get_discord_config(self) -> dict[str, Any]:
        return load_config("discord_config")

    def get_values_config(self) -> dict[str, Any]:
        return load_config("values_config")

    def get_strings_config(self) -> dict[str, Any]:
        return load_config("strings_config")

    def get_schedule_config(self) -> dict[str, Any]:
        return load_config("schedule_config")

    def load_config(self, name: str) -> dict[str, Any]:
        return load_config(name)

    def get_value(self, config_name: str, key: str, default: Any = None) -> Any:
        data = self.load_config(config_name)
        return data.get(key, os.getenv(key.upper(), default))

    def clear_cache(self) -> None:
        _CONFIG_CACHE.clear()


config_manager = ConfigManager()


def get_discord_config() -> dict[str, Any]:
    return config_manager.get_discord_config()


def get_values_config() -> dict[str, Any]:
    return config_manager.get_values_config()


def debug_log(action: str, log_type: str = "general") -> None:
    """Log a debug message with caller context (backward compatible)."""
    import inspect
    caller = inspect.stack()[1].function
    log = logging.getLogger("astra." + log_type)
    log.debug("[DEBUG] %s in %s...", action, caller)
