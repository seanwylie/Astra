# beta_config.py

"""
⚙️ Beta Configuration System
----------------------------
Centralized configuration management for the modern Astra beta implementation.

Provides:
- Unified config loading with caching
- Environment variable integration
- Default value handling
- Configuration validation

Author: Sean Wylie
Created: 2025-04-14
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Configuration cache
_config_cache: Dict[str, Dict[str, Any]] = {}

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "astra_core" / "config"


class ConfigManager:
    """Centralized configuration manager for beta Astra."""
    
    def __init__(self):
        self._cache = {}
        self._config_dir = CONFIG_DIR
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file with caching and validation.
        
        Args:
            config_name: Name of config file (with or without .json extension)
            
        Returns:
            Configuration dictionary
        """
        if not config_name.endswith('.json'):
            config_name += '.json'
            
        if config_name in self._cache:
            return self._cache[config_name]
            
        config_path = self._config_dir / config_name
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Validate configuration
                if self._validate_config(config_name, config):
                    self._cache[config_name] = config
                    return config
                else:
                    print(f"⚠️ Configuration validation failed for {config_name}")
                    return {}
                    
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {config_path}: {e}")
            return {}
    
    def _validate_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        Validate configuration based on expected structure.
        
        Args:
            config_name: Name of the config file
            config: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Define expected keys for different config types
        validation_rules = {
            'discord_config.json': ['discord_channel'],
            'values_config.json': ['values'],
            'schedule_config.json': [],  # Schedule config is flexible
            'strings_config.json': ['responses', 'emojis'],
        }
        
        required_keys = validation_rules.get(config_name, [])
        
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key '{key}' in {config_name}")
                return False
        
        return True
    
    def get_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        Get a specific value from a config file.
        
        Args:
            config_name: Name of config file
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load_config(config_name)
        return config.get(key, os.getenv(key.upper(), default))
    
    def get_discord_config(self) -> Dict[str, Any]:
        """Get Discord-specific configuration."""
        return self.load_config("discord_config")
    
    def get_values_config(self) -> Dict[str, Any]:
        """Get values configuration."""
        return self.load_config("values_config")
    
    def get_strings_config(self) -> Dict[str, Any]:
        """Get strings configuration."""
        return self.load_config("strings_config")
    
    def get_schedule_config(self) -> Dict[str, Any]:
        """Get schedule configuration."""
        return self.load_config("schedule_config")
    
    def clear_cache(self):
        """Clear the configuration cache."""
        self._cache.clear()


# Global config manager instance
config_manager = ConfigManager()

# Convenience functions
def load_config(config_name: str) -> Dict[str, Any]:
    """Load a configuration file."""
    return config_manager.load_config(config_name)

def get_config_value(config_name: str, key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    return config_manager.get_value(config_name, key, default)