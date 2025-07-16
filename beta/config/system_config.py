"""
System Configuration for Astra Beta
Centralizes all system settings, limits, and configurable values.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class SystemLimits:
    """System-wide limits and constraints"""
    # Memory System Limits
    MAX_MEMORY_KEY_LENGTH: int = 100
    MAX_MEMORY_VALUE_LENGTH: int = 1000
    MAX_MEMORIES_PER_USER: int = 1000
    MAX_CONTEXT_LENGTH: int = 50
    MEMORY_SEARCH_SIMILARITY_THRESHOLD: int = 60
    MEMORY_FUZZY_MATCH_THRESHOLD: int = 60
    
    # Creative System Limits
    MAX_CREATIVE_HISTORY_LENGTH: int = 100
    MAX_POEM_TOPIC_LENGTH: int = 100
    MAX_STORY_PROMPT_LENGTH: int = 500
    MAX_ART_DESCRIPTION_LENGTH: int = 200
    MAX_CREATIVE_EXERCISE_LENGTH: int = 1000
    
    # Learning System Limits
    MAX_LEARNING_CONTENT_LENGTH: int = 10000
    MAX_LEARNING_SESSIONS: int = 1000
    MAX_QUIZ_QUESTIONS: int = 10
    MIN_QUIZ_QUESTIONS: int = 1
    MAX_STUDY_PLAN_WEEKS: int = 52
    MAX_CONCEPTS_PER_SESSION: int = 10
    MAX_KEY_POINTS_PER_SESSION: int = 5
    
    # Analytics System Limits
    MAX_ANALYTICS_HISTORY_DAYS: int = 365
    MIN_ANALYTICS_HISTORY_DAYS: int = 1
    MAX_ACHIEVEMENT_CATEGORIES: int = 10
    MAX_RECOMMENDATIONS_PER_CATEGORY: int = 5
    
    # General System Limits
    MAX_MESSAGE_CHUNK_SIZE: int = 2000
    MAX_COMMAND_ARGS: int = 20
    MAX_USER_ID_LENGTH: int = 50
    MAX_SESSION_ID_LENGTH: int = 100

@dataclass
class SystemDefaults:
    """Default values for system operations"""
    # Memory System Defaults
    DEFAULT_MEMORY_LIMIT: int = 5
    DEFAULT_CONTEXT_LIMIT: int = 10
    DEFAULT_SEARCH_LIMIT: int = 5
    
    # Creative System Defaults
    DEFAULT_CREATIVE_HISTORY_LIMIT: int = 5
    DEFAULT_QUIZ_DIFFICULTY: str = "medium"
    DEFAULT_QUIZ_QUESTIONS: int = 5
    
    # Learning System Defaults
    DEFAULT_STUDY_TIMEFRAME: str = "1 month"
    DEFAULT_GROWTH_REPORT_DAYS: int = 30
    DEFAULT_ACTIVITY_SUMMARY_DAYS: int = 7
    DEFAULT_COMPARISON_DAYS: int = 30
    
    # Analytics System Defaults
    DEFAULT_ANALYTICS_LIMIT: int = 10
    DEFAULT_STATS_PRECISION: int = 1
    
    # Personality System Defaults
    DEFAULT_PERSONALITY_MODE: str = "balanced"

@dataclass
class FileSystemConfig:
    """File system configuration"""
    # Data Files
    MEMORY_DATA_FILE: str = "data/user_memories.json"
    LEARNING_DATA_FILE: str = "data/learning_data.json"
    ANALYTICS_DATA_FILE: str = "data/analytics_data.json"
    CREATIVE_HISTORY_FILE: str = "creative_history.json"
    
    # Log Files
    LOG_DIRECTORY: str = "logs"
    MAIN_LOG_FILE: str = "astra_beta.log"
    ERROR_LOG_FILE: str = "astra_errors.log"
    
    # Backup Configuration
    BACKUP_DIRECTORY: str = "__backups__"
    MAX_BACKUP_FILES: int = 10
    BACKUP_INTERVAL_HOURS: int = 24

@dataclass
class APIConfig:
    """API configuration and limits"""
    # OpenAI Configuration
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = 30
    
    # Discord Configuration
    DISCORD_MAX_MESSAGE_LENGTH: int = 2000
    DISCORD_RATE_LIMIT_DELAY: float = 1.0
    DISCORD_RECONNECT_ATTEMPTS: int = 5
    
    # External API Timeouts
    WIKIPEDIA_TIMEOUT: int = 10
    WEB_SCRAPING_TIMEOUT: int = 15
    S3_OPERATION_TIMEOUT: int = 30

@dataclass
class PerformanceConfig:
    """Performance and optimization settings"""
    # Caching Configuration
    ENABLE_CONFIG_CACHING: bool = True
    CONFIG_CACHE_TTL: int = 3600  # 1 hour
    ENABLE_ANALYTICS_CACHING: bool = True
    ANALYTICS_CACHE_TTL: int = 300  # 5 minutes
    
    # Processing Limits
    MAX_CONCURRENT_OPERATIONS: int = 10
    BATCH_PROCESSING_SIZE: int = 100
    MEMORY_CLEANUP_INTERVAL: int = 3600  # 1 hour
    
    # Database/Storage Optimization
    AUTO_SAVE_INTERVAL: int = 60  # 1 minute
    BULK_SAVE_THRESHOLD: int = 10
    COMPRESSION_ENABLED: bool = True

class SystemConfig:
    """Main system configuration class"""
    
    def __init__(self):
        self.limits = SystemLimits()
        self.defaults = SystemDefaults()
        self.filesystem = FileSystemConfig()
        self.api = APIConfig()
        self.performance = PerformanceConfig()
        self.environment = self._load_environment_config()
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # Discord Configuration
            "DISCORD_TOKEN": os.getenv("TOKEN"),
            "DISCORD_GUILD_ID": os.getenv("GUILD_ID"),
            
            # OpenAI Configuration
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "OPENAI_ORG_ID": os.getenv("OPENAI_ORG_ID"),
            
            # AWS Configuration
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
            "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
            
            # System Configuration
            "DEBUG_MODE": os.getenv("DEBUG", "false").lower() == "true",
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            
            # Feature Flags
            "ENABLE_ANALYTICS": os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            "ENABLE_CREATIVE": os.getenv("ENABLE_CREATIVE", "true").lower() == "true",
            "ENABLE_LEARNING": os.getenv("ENABLE_LEARNING", "true").lower() == "true",
            "ENABLE_MEMORY": os.getenv("ENABLE_MEMORY", "true").lower() == "true",
        }
    
    def get_personality_modes(self) -> List[str]:
        """Get list of available personality modes"""
        return ["curious", "analytical", "creative", "mentor", "philosophical", "balanced"]
    
    def get_creative_types(self) -> List[str]:
        """Get list of available creative types"""
        return ["poem", "story", "art_prompt", "music", "exercise"]
    
    def get_quiz_difficulties(self) -> List[str]:
        """Get list of available quiz difficulties"""
        return ["easy", "medium", "hard"]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return ["en"]  # Can be extended for future language support
    
    def validate_config(self) -> List[str]:
        """Validate system configuration and return any issues"""
        issues = []
        
        # Check required environment variables
        required_env_vars = ["DISCORD_TOKEN", "OPENAI_API_KEY"]
        for var in required_env_vars:
            if not self.environment.get(var):
                issues.append(f"Missing required environment variable: {var}")
        
        # Validate limits
        if self.limits.MAX_MEMORY_KEY_LENGTH <= 0:
            issues.append("MAX_MEMORY_KEY_LENGTH must be positive")
        
        if self.limits.MAX_MESSAGE_CHUNK_SIZE <= 0:
            issues.append("MAX_MESSAGE_CHUNK_SIZE must be positive")
        
        # Validate file paths
        if not os.path.exists(self.filesystem.LOG_DIRECTORY):
            try:
                os.makedirs(self.filesystem.LOG_DIRECTORY, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create log directory: {e}")
        
        return issues
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get current feature flag settings"""
        return {
            "analytics": self.environment.get("ENABLE_ANALYTICS", True),
            "creative": self.environment.get("ENABLE_CREATIVE", True),
            "learning": self.environment.get("ENABLE_LEARNING", True),
            "memory": self.environment.get("ENABLE_MEMORY", True),
        }
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.environment.get("DEBUG_MODE", False)
    
    def get_log_level(self) -> str:
        """Get current log level"""
        return self.environment.get("LOG_LEVEL", "INFO")

# Global system configuration instance
system_config = SystemConfig()

def get_system_config() -> SystemConfig:
    """Get the global system configuration"""
    return system_config

def validate_system_config() -> List[str]:
    """Validate system configuration"""
    return system_config.validate_config()