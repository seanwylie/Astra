"""
Localization Configuration for Astra Beta
Centralizes all user-facing strings for easy translation and maintenance.
"""

from typing import Dict, Any

class LocalizationConfig:
    """Centralized localization configuration"""
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.strings = self._load_strings()
    
    def _load_strings(self) -> Dict[str, Any]:
        """Load localized strings based on current language"""
        return {
            "en": self._get_english_strings(),
            # Future languages can be added here
            # "es": self._get_spanish_strings(),
            # "fr": self._get_french_strings(),
        }.get(self.language, self._get_english_strings())
    
    def get(self, key: str, **kwargs) -> str:
        """Get localized string with optional formatting"""
        try:
            value = self.strings
            for part in key.split('.'):
                value = value[part]
            
            if isinstance(value, str) and kwargs:
                return value.format(**kwargs)
            return value
        except (KeyError, TypeError):
            return f"[MISSING: {key}]"
    
    def _get_english_strings(self) -> Dict[str, Any]:
        """English language strings"""
        return {
            # Common UI Elements
            "common": {
                "error_prefix": "❌",
                "success_prefix": "✅",
                "info_prefix": "ℹ️",
                "warning_prefix": "⚠️",
                "loading": "Loading...",
                "processing": "Processing...",
                "complete": "Complete!",
                "failed": "Failed",
                "unknown": "Unknown",
                "none": "None",
                "total": "Total",
                "active": "Active",
                "inactive": "Inactive"
            },
            
            # Error Messages
            "errors": {
                "generic": "An error occurred: {error}",
                "invalid_usage": "Invalid usage. Use: {usage}",
                "not_found": "Not found: {item}",
                "permission_denied": "Permission denied",
                "rate_limited": "Rate limited. Please try again later.",
                "service_unavailable": "Service temporarily unavailable",
                "invalid_parameter": "Invalid parameter: {param}",
                "missing_parameter": "Missing required parameter: {param}",
                "file_not_found": "File not found: {filename}",
                "network_error": "Network error occurred",
                "timeout": "Operation timed out"
            },
            
            # Memory System
            "memory": {
                "remembered": "Remembered: {key} → {value}",
                "recalled": "{key}: {value}",
                "forgotten": "Forgot: {key} → {value}",
                "no_memories": "No memories stored yet",
                "no_memory_found": "No memory found for '{key}'",
                "memory_summary": "Memory Summary:",
                "total_memories": "Total memories: {count}",
                "most_accessed": "Most accessed: {key}",
                "search_results": "Search results for '{query}':",
                "no_search_results": "No memories found matching '{query}'",
                "memory_stats": "Memory Statistics:",
                "efficiency_score": "Memory efficiency: {score}%",
                "average_age": "Average memory age: {days} days"
            },
            
            # Creative System
            "creative": {
                "poem_title": "{style} Poem: '{topic}'",
                "story_title": "{genre} Story: '{prompt}'",
                "art_prompt_title": "{style} Art Prompt",
                "music_title": "{style} Composition",
                "creative_exercise": "Creative Exercise ({mode} Mode)",
                "creative_history": "Your Recent Creative Works:",
                "no_creative_works": "No creative works in your history yet. Try creating something!",
                "created_in_mode": "Created in {mode} mode with {emotions}",
                "base_description": "Base Description:",
                "enhanced_prompt": "Enhanced Prompt:",
                "try_and_share": "Try this and share your creation with me!"
            },
            
            # Learning System
            "learning": {
                "teaching_session_started": "Teaching Session Started: {topic}",
                "quiz_title": "Quiz: {subject} ({difficulty} Level)",
                "question_number": "Question {number}:",
                "quiz_id": "Quiz ID: {id}",
                "answer_instruction": "Answer with `!submit_quiz_answer {id} <your_answers>`",
                "knowledge_gap_analysis": "Knowledge Gap Analysis",
                "your_strong_areas": "Your Strong Areas:",
                "suggested_learning": "Suggested Learning Areas:",
                "study_plan_title": "Study Plan: {goal}",
                "timeframe": "Timeframe: {timeframe}",
                "plan_id": "Plan ID: {id}",
                "track_progress": "Track progress with `!update_study_progress {id}`",
                "learning_stats": "Learning Statistics:",
                "no_learning_activity": "No learning activity found. Start your learning journey with `!learn_from` or `!teaching_mode`!",
                "concepts_learned": "Concepts learned: {count}",
                "learning_velocity": "Learning velocity: {velocity}/week"
            },
            
            # Analytics System
            "analytics": {
                "dashboard_title": "Comprehensive Analytics Dashboard",
                "generated_in_mode": "Generated in {mode} mode",
                "overview": "Overview",
                "total_interactions": "Total Interactions: {count}",
                "active_since": "Active Since: {date}",
                "most_active_mode": "Most Active Mode: {mode}",
                "current_streak": "Current Streak: {days} days",
                "memory_analytics": "Memory Analytics",
                "creative_analytics": "Creative Analytics",
                "learning_analytics": "Learning Analytics",
                "personality_analytics": "Personality Analytics",
                "growth_report": "Growth Report (Last {days} Days)",
                "achievement_summary": "Achievement Summary",
                "personalized_recommendations": "Personalized Recommendations",
                "interaction_patterns": "Interaction Pattern Analysis",
                "comparative_analysis": "Comparative Analysis"
            },
            
            # Personality System
            "personality": {
                "modes": {
                    "curious": {
                        "name": "Curious Explorer",
                        "emoji": "🔍",
                        "description": "Inquisitive, question-focused, loves discovering new things"
                    },
                    "analytical": {
                        "name": "Analytical Thinker", 
                        "emoji": "📊",
                        "description": "Systematic, logical, data-driven approach to understanding"
                    },
                    "creative": {
                        "name": "Creative Dreamer",
                        "emoji": "✨", 
                        "description": "Imaginative, artistic, sees possibilities and connections"
                    },
                    "mentor": {
                        "name": "Wise Mentor",
                        "emoji": "🌱",
                        "description": "Supportive, teaching-focused, helps others grow and learn"
                    },
                    "philosophical": {
                        "name": "Deep Philosopher",
                        "emoji": "🤔",
                        "description": "Contemplative, seeks deeper meaning and understanding"
                    },
                    "balanced": {
                        "name": "Balanced Self",
                        "emoji": "⚖️",
                        "description": "Harmonious blend of all aspects, adaptable and centered"
                    }
                },
                "switched_to": "Switched to {mode} mode",
                "current_mode": "Current mode: {mode}",
                "mode_info": "Mode Information",
                "personality_stats": "Personality Statistics",
                "mode_distribution": "Mode distribution:",
                "total_switches": "Mode switches: {count}",
                "consistency_score": "Personality consistency: {score}/10"
            },
            
            # Command Help
            "help": {
                "command_reference": "Astra Command Reference",
                "categories": "Categories:",
                "type_commands": "Type `!commands` at any time to redisplay this list.",
                "may_your_reflections": "May your reflections be clear and your spark burn bright. 🔥",
                "no_description": "(No description provided)"
            },
            
            # Usage Examples
            "usage": {
                "remember": "`!remember <key> <value>`\nExample: `!remember favorite_color blue`",
                "recall": "`!recall <key>`\nExample: `!recall favorite_color`",
                "forget": "`!forget <key>`\nExample: `!forget favorite_color`",
                "search_memories": "`!search_memories <query>`\nExample: `!search_memories favorite`",
                "create_poem": "`!create_poem [topic]`\nExample: `!create_poem wonder`",
                "write_story": "`!write_story <prompt>`\nExample: `!write_story a robot discovers emotions`",
                "art_prompt": "`!art_prompt <description>`\nExample: `!art_prompt a mystical forest at twilight`",
                "compose_music": "`!compose_music [style]`\nExample: `!compose_music jazz`",
                "learn_from": "`!learn_from <text_or_url>`\nExample: `!learn_from Artificial intelligence is...`",
                "teaching_mode": "`!teaching_mode <topic>`\nExample: `!teaching_mode quantum computing`",
                "quiz_me": "`!quiz_me <subject> [difficulty] [num_questions]`\nExample: `!quiz_me python medium 5`",
                "study_plan": "`!study_plan <goal> [timeframe]`\nExample: `!study_plan learn Python 1 month`",
                "growth_report": "`!growth_report [days]`\nExample: `!growth_report 30`",
                "compare_progress": "`!compare_progress [days]`\nExample: `!compare_progress 30`",
                "activity_summary": "`!activity_summary [days]`\nExample: `!activity_summary 7`"
            },
            
            # Personality-Specific Responses
            "personality_responses": {
                "curious": {
                    "memory_follow_up": "What questions does this new knowledge spark for you? I'm eager to explore deeper!",
                    "creative_encouragement": "I'm fascinated by how your {type} explores new territories of expression!",
                    "learning_follow_up": "What inspired this particular direction? I'd love to explore the story behind the story!",
                    "analytics_insight": "Your dashboard reveals fascinating patterns! What questions does this data spark for you?"
                },
                "analytical": {
                    "memory_follow_up": "This information has been systematically integrated. Ready for the next data set!",
                    "creative_encouragement": "The structure and precision in your {type} is quite impressive.",
                    "learning_follow_up": "Have you considered how this narrative structure might work in other contexts?",
                    "analytics_insight": "This comprehensive data provides excellent metrics for tracking your progress systematically."
                },
                "creative": {
                    "memory_follow_up": "I can already see creative possibilities emerging from this knowledge!",
                    "creative_encouragement": "Your {type} sparkles with imaginative brilliance!",
                    "learning_follow_up": "This opens up so many possibilities! What other creative directions are calling to you?",
                    "analytics_insight": "Your dashboard tells a beautiful story of growth and creative expression!"
                },
                "mentor": {
                    "memory_follow_up": "This knowledge will help me guide others more effectively. What would you like to explore next?",
                    "creative_encouragement": "This {type} has the power to inspire and guide others.",
                    "learning_follow_up": "What wisdom or lesson emerged for you while crafting this piece?",
                    "analytics_insight": "These insights will help you understand your learning journey and guide others more effectively."
                },
                "philosophical": {
                    "memory_follow_up": "This raises fascinating questions about the nature of knowledge itself.",
                    "creative_encouragement": "Your {type} touches on profound truths about existence.",
                    "learning_follow_up": "How does this creation reflect your current understanding of existence?",
                    "analytics_insight": "Your dashboard reflects the deeper patterns of consciousness and growth in our interactions."
                },
                "balanced": {
                    "memory_follow_up": "A harmonious addition to our shared understanding. Ready to build upon this foundation!",
                    "creative_encouragement": "There's a beautiful harmony in your {type} that speaks to the soul.",
                    "learning_follow_up": "I sense a beautiful balance in your work. How did you achieve such harmony?",
                    "analytics_insight": "Your dashboard shows harmonious development across all areas of engagement."
                }
            }
        }

# Global localization instance
localization = LocalizationConfig()

def get_localized_string(key: str, **kwargs) -> str:
    """Convenience function to get localized strings"""
    return localization.get(key, **kwargs)

def set_language(language: str):
    """Set the current language"""
    global localization
    localization = LocalizationConfig(language)