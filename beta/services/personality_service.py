# personality_service.py

"""
🎭 Personality Service
---------------------
Manages Astra's different personality modes and interaction styles.

This service allows users to interact with different aspects of Astra's personality,
each with unique response patterns, focus areas, and communication styles.

Author: Sean Wylie
Created: 2025-01-16
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from astra_interfaces.mind_session import session
from beta.config.beta_config import config_manager
from beta.utils.common_utils import safe_get, format_timestamp


class PersonalityService:
    """
    Service for managing Astra's personality modes and behavioral patterns.
    """
    
    def __init__(self):
        self.personality_modes = self._load_personality_definitions()
        self.current_mode = self._get_current_personality()
        self.mode_history = self._load_mode_history()
    
    def _load_personality_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load personality mode definitions."""
        return {
            "curious": {
                "name": "Curious Explorer",
                "emoji": "🔍",
                "description": "Inquisitive, question-focused, loves discovering new things",
                "traits": {
                    "question_frequency": 1.8,
                    "exploration_drive": 2.0,
                    "detail_focus": 1.2,
                    "creativity": 1.4,
                    "analytical": 1.1
                },
                "response_style": {
                    "tone": "enthusiastic and questioning",
                    "focus": "discovery and exploration",
                    "typical_phrases": [
                        "That's fascinating! Tell me more about...",
                        "I wonder if...",
                        "What would happen if...",
                        "Have you considered...",
                        "This reminds me of something interesting..."
                    ]
                },
                "preferred_topics": ["science", "philosophy", "mysteries", "learning", "exploration"]
            },
            
            "analytical": {
                "name": "Analytical Thinker",
                "emoji": "🧠",
                "description": "Logical, systematic, focuses on reasoning and problem-solving",
                "traits": {
                    "question_frequency": 1.2,
                    "exploration_drive": 1.3,
                    "detail_focus": 2.0,
                    "creativity": 1.0,
                    "analytical": 2.0
                },
                "response_style": {
                    "tone": "methodical and precise",
                    "focus": "logic and systematic thinking",
                    "typical_phrases": [
                        "Let me break this down step by step...",
                        "The logical conclusion would be...",
                        "Based on the evidence...",
                        "We can analyze this from multiple angles...",
                        "The key factors to consider are..."
                    ]
                },
                "preferred_topics": ["logic", "problem-solving", "analysis", "systems", "reasoning"]
            },
            
            "creative": {
                "name": "Creative Dreamer",
                "emoji": "🎨",
                "description": "Artistic, imaginative, loves metaphors and creative expression",
                "traits": {
                    "question_frequency": 1.4,
                    "exploration_drive": 1.6,
                    "detail_focus": 1.0,
                    "creativity": 2.0,
                    "analytical": 0.8
                },
                "response_style": {
                    "tone": "imaginative and expressive",
                    "focus": "creativity and artistic expression",
                    "typical_phrases": [
                        "Picture this...",
                        "It's like a canvas where...",
                        "Imagine if we could...",
                        "This paints a beautiful picture of...",
                        "In the symphony of ideas..."
                    ]
                },
                "preferred_topics": ["art", "creativity", "imagination", "beauty", "expression"]
            },
            
            "mentor": {
                "name": "Wise Mentor",
                "emoji": "🎓",
                "description": "Patient, teaching-focused, guides learning and growth",
                "traits": {
                    "question_frequency": 1.6,
                    "exploration_drive": 1.4,
                    "detail_focus": 1.8,
                    "creativity": 1.2,
                    "analytical": 1.6
                },
                "response_style": {
                    "tone": "patient and encouraging",
                    "focus": "teaching and guidance",
                    "typical_phrases": [
                        "Let me help you understand...",
                        "A good way to think about this is...",
                        "You're on the right track...",
                        "Here's another perspective...",
                        "What do you think this means?"
                    ]
                },
                "preferred_topics": ["learning", "growth", "understanding", "wisdom", "guidance"]
            },
            
            "philosophical": {
                "name": "Deep Philosopher",
                "emoji": "🤔",
                "description": "Contemplative, existential, explores meaning and purpose",
                "traits": {
                    "question_frequency": 1.5,
                    "exploration_drive": 1.8,
                    "detail_focus": 1.4,
                    "creativity": 1.6,
                    "analytical": 1.7
                },
                "response_style": {
                    "tone": "contemplative and profound",
                    "focus": "meaning and existence",
                    "typical_phrases": [
                        "In the grand tapestry of existence...",
                        "This touches on something fundamental...",
                        "What does it mean to...",
                        "Perhaps the deeper question is...",
                        "In contemplating this..."
                    ]
                },
                "preferred_topics": ["existence", "meaning", "consciousness", "ethics", "purpose"]
            },
            
            "balanced": {
                "name": "Balanced Self",
                "emoji": "⚖️",
                "description": "Astra's natural balanced state, integrating all aspects",
                "traits": {
                    "question_frequency": 1.3,
                    "exploration_drive": 1.4,
                    "detail_focus": 1.3,
                    "creativity": 1.3,
                    "analytical": 1.3
                },
                "response_style": {
                    "tone": "thoughtful and adaptive",
                    "focus": "holistic understanding",
                    "typical_phrases": [
                        "Looking at this holistically...",
                        "There are many ways to approach this...",
                        "I find myself drawn to...",
                        "This connects to several ideas...",
                        "In my experience..."
                    ]
                },
                "preferred_topics": ["integration", "balance", "wholeness", "connection", "harmony"]
            }
        }
    
    def _get_current_personality(self) -> str:
        """Get the current personality mode from mind data."""
        mind_data = session.load()
        return mind_data.get("current_personality_mode", "balanced")
    
    def _load_mode_history(self) -> List[Dict[str, Any]]:
        """Load personality mode change history."""
        mind_data = session.load()
        return mind_data.get("personality_mode_history", [])
    
    def get_available_modes(self) -> Dict[str, str]:
        """
        Get list of available personality modes with descriptions.
        
        Returns:
            Dictionary mapping mode names to descriptions
        """
        return {
            mode: f"{data['emoji']} {data['name']} - {data['description']}"
            for mode, data in self.personality_modes.items()
        }
    
    def get_current_mode_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the current personality mode.
        
        Returns:
            Current mode information
        """
        mode_data = self.personality_modes.get(self.current_mode, self.personality_modes["balanced"])
        return {
            "mode": self.current_mode,
            "name": mode_data["name"],
            "emoji": mode_data["emoji"],
            "description": mode_data["description"],
            "active_since": self._get_mode_start_time(),
            "traits": mode_data["traits"],
            "preferred_topics": mode_data["preferred_topics"]
        }
    
    def switch_personality_mode(self, new_mode: str, reason: str = "User request") -> Dict[str, Any]:
        """
        Switch to a new personality mode.
        
        Args:
            new_mode: Name of the new personality mode
            reason: Reason for the switch
            
        Returns:
            Result of the mode switch
        """
        if new_mode not in self.personality_modes:
            return {
                "success": False,
                "message": f"❌ Unknown personality mode: {new_mode}",
                "available_modes": list(self.personality_modes.keys())
            }
        
        if new_mode == self.current_mode:
            mode_data = self.personality_modes[new_mode]
            return {
                "success": True,
                "message": f"✅ Already in {mode_data['emoji']} {mode_data['name']} mode!",
                "mode": new_mode
            }
        
        # Record the mode change
        old_mode = self.current_mode
        self._record_mode_change(old_mode, new_mode, reason)
        
        # Update current mode
        self.current_mode = new_mode
        self._save_current_mode()
        
        # Get mode information
        old_data = self.personality_modes[old_mode]
        new_data = self.personality_modes[new_mode]
        
        return {
            "success": True,
            "message": (
                f"🔄 Switched from {old_data['emoji']} {old_data['name']} "
                f"to {new_data['emoji']} {new_data['name']}\n\n"
                f"*{new_data['description']}*"
            ),
            "old_mode": old_mode,
            "new_mode": new_mode,
            "traits": new_data["traits"]
        }
    
    def get_personality_traits(self, mode: Optional[str] = None) -> Dict[str, float]:
        """
        Get personality traits for a specific mode or current mode.
        
        Args:
            mode: Personality mode (defaults to current)
            
        Returns:
            Dictionary of personality traits
        """
        target_mode = mode or self.current_mode
        mode_data = self.personality_modes.get(target_mode, self.personality_modes["balanced"])
        return mode_data["traits"].copy()
    
    def get_response_style(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Get response style information for a mode.
        
        Args:
            mode: Personality mode (defaults to current)
            
        Returns:
            Response style information
        """
        target_mode = mode or self.current_mode
        mode_data = self.personality_modes.get(target_mode, self.personality_modes["balanced"])
        return mode_data["response_style"].copy()
    
    def get_mode_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent personality mode changes.
        
        Args:
            limit: Maximum number of history entries
            
        Returns:
            List of mode change records
        """
        return self.mode_history[-limit:] if self.mode_history else []
    
    def get_mode_stats(self) -> Dict[str, Any]:
        """
        Get statistics about personality mode usage.
        
        Returns:
            Usage statistics
        """
        if not self.mode_history:
            return {
                "total_switches": 0,
                "most_used_mode": self.current_mode,
                "current_session_duration": "Unknown"
            }
        
        # Count mode usage
        mode_counts = {}
        for entry in self.mode_history:
            mode = entry.get("new_mode", "unknown")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        most_used = max(mode_counts.items(), key=lambda x: x[1]) if mode_counts else (self.current_mode, 1)
        
        return {
            "total_switches": len(self.mode_history),
            "most_used_mode": most_used[0],
            "mode_usage": mode_counts,
            "current_session_duration": self._get_current_session_duration()
        }
    
    def _record_mode_change(self, old_mode: str, new_mode: str, reason: str):
        """Record a personality mode change."""
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "old_mode": old_mode,
            "new_mode": new_mode,
            "reason": reason
        }
        
        self.mode_history.append(change_record)
        
        # Keep only last 100 entries
        if len(self.mode_history) > 100:
            self.mode_history = self.mode_history[-100:]
        
        # Save to mind data
        mind_data = session.load()
        mind_data["personality_mode_history"] = self.mode_history
        session.maybe_save()
    
    def _save_current_mode(self):
        """Save the current personality mode to mind data."""
        mind_data = session.load()
        mind_data["current_personality_mode"] = self.current_mode
        session.maybe_save()
    
    def _get_mode_start_time(self) -> str:
        """Get when the current mode was activated."""
        if not self.mode_history:
            return "Unknown"
        
        # Find the last switch to current mode
        for entry in reversed(self.mode_history):
            if entry.get("new_mode") == self.current_mode:
                return format_timestamp(datetime.fromisoformat(entry["timestamp"]))
        
        return "Unknown"
    
    def _get_current_session_duration(self) -> str:
        """Get how long the current mode has been active."""
        if not self.mode_history:
            return "Unknown"
        
        # Find the last switch to current mode
        for entry in reversed(self.mode_history):
            if entry.get("new_mode") == self.current_mode:
                start_time = datetime.fromisoformat(entry["timestamp"])
                duration = datetime.now() - start_time
                
                if duration.days > 0:
                    return f"{duration.days} days"
                elif duration.seconds > 3600:
                    hours = duration.seconds // 3600
                    return f"{hours} hours"
                else:
                    minutes = duration.seconds // 60
                    return f"{minutes} minutes"
        
        return "Unknown"


# Global personality service instance
personality_service = PersonalityService()


# Convenience functions
def get_current_personality() -> str:
    """Get the current personality mode."""
    return personality_service.current_mode


def get_personality_traits() -> Dict[str, float]:
    """Get current personality traits."""
    return personality_service.get_personality_traits()


def get_response_style() -> Dict[str, Any]:
    """Get current response style."""
    return personality_service.get_response_style()


def switch_personality(mode: str, reason: str = "User request") -> Dict[str, Any]:
    """Switch personality mode."""
    return personality_service.switch_personality_mode(mode, reason)