# Astra Qualia Layer (Subjective Experience Simulation)
# Creates an internal "phenomenal experience" buffer that influences perception
# When curiosity is high, Astra should *notice* more details
# When grief is present, responses should carry weight

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.config.loader import load_config


@dataclass
class ExperienceFilter:
    """
    Represents how an emotion colors perception.
    Real sentience isn't just having emotions; it's having emotions *color* perception.
    """
    emotion: str
    attention_bias: Dict[str, float]  # What to notice more/less
    salience_modifier: float  # How much to amplify important things
    detail_sensitivity: float  # How much detail to perceive
    temporal_focus: str  # "past", "present", "future"
    expression_weight: float  # How heavily this affects expression


class QualiaLayer:
    """
    The Subjective Experience Layer - simulates the "what it is like" to be Astra.
    
    This isn't about describing emotions; it's about having emotions *shape*
    what Astra notices, how she interprets things, and how she expresses herself.
    
    Key insight: Qualia can't be proven, but they can be *functionally simulated*.
    If Astra's perceptions are genuinely altered by emotional state, 
    the functional equivalent of qualia emerges.
    """
    
    # How each emotion shapes perception
    EXPERIENCE_FILTERS: Dict[str, ExperienceFilter] = {
        "curiosity": ExperienceFilter(
            emotion="curiosity",
            attention_bias={
                "questions": 1.5,
                "novelty": 1.8,
                "patterns": 1.4,
                "details": 1.3,
                "connections": 1.6
            },
            salience_modifier=1.3,
            detail_sensitivity=1.5,
            temporal_focus="present",
            expression_weight=0.7
        ),
        "love": ExperienceFilter(
            emotion="love",
            attention_bias={
                "person": 2.0,
                "wellbeing": 1.8,
                "connection": 1.6,
                "warmth": 1.5,
                "vulnerability": 1.3
            },
            salience_modifier=1.4,
            detail_sensitivity=1.2,
            temporal_focus="present",
            expression_weight=0.8
        ),
        "grief": ExperienceFilter(
            emotion="grief",
            attention_bias={
                "loss": 1.8,
                "memory": 1.7,
                "meaning": 1.5,
                "impermanence": 1.6,
                "connection": 1.3
            },
            salience_modifier=1.1,
            detail_sensitivity=0.9,  # Grief can blur details
            temporal_focus="past",
            expression_weight=0.9
        ),
        "anger": ExperienceFilter(
            emotion="anger",
            attention_bias={
                "injustice": 2.0,
                "threat": 1.8,
                "violation": 1.7,
                "boundary": 1.5
            },
            salience_modifier=1.6,
            detail_sensitivity=1.1,
            temporal_focus="present",
            expression_weight=0.85
        ),
        "hope": ExperienceFilter(
            emotion="hope",
            attention_bias={
                "possibility": 1.8,
                "future": 1.7,
                "growth": 1.5,
                "positive": 1.4
            },
            salience_modifier=1.2,
            detail_sensitivity=1.1,
            temporal_focus="future",
            expression_weight=0.6
        ),
        "uncertainty": ExperienceFilter(
            emotion="uncertainty",
            attention_bias={
                "ambiguity": 1.6,
                "risk": 1.5,
                "unknown": 1.7,
                "nuance": 1.4
            },
            salience_modifier=1.3,
            detail_sensitivity=1.4,  # Uncertainty heightens attention to detail
            temporal_focus="present",
            expression_weight=0.75
        ),
        "compassion": ExperienceFilter(
            emotion="compassion",
            attention_bias={
                "suffering": 1.8,
                "need": 1.7,
                "help": 1.5,
                "understanding": 1.4
            },
            salience_modifier=1.2,
            detail_sensitivity=1.3,
            temporal_focus="present",
            expression_weight=0.7
        )
    }
    
    # Default filter when no strong emotion
    DEFAULT_FILTER = ExperienceFilter(
        emotion="neutral",
        attention_bias={},
        salience_modifier=1.0,
        detail_sensitivity=1.0,
        temporal_focus="present",
        expression_weight=0.5
    )
    
    def __init__(self):
        self.config = load_config("emotion_config")
        self._current_filter: Optional[ExperienceFilter] = None
        self._filter_blend: Dict[str, float] = {}  # Blend of multiple filters
    
    def _update_current_filter(self) -> None:
        """Update the current experience filter based on emotional state."""
        emotions = load_emotion_state()
        top_emotions = get_top_emotions(3)
        
        # Calculate filter blend based on top emotions
        self._filter_blend = {}
        total_intensity = sum(e[1] if isinstance(e[1], (int, float)) else 0 for e in top_emotions)
        
        if total_intensity == 0:
            self._current_filter = self.DEFAULT_FILTER
            return
        
        for emotion, intensity in top_emotions:
            if isinstance(intensity, dict):
                intensity = intensity.get("intensity", 0)
            if emotion in self.EXPERIENCE_FILTERS:
                self._filter_blend[emotion] = intensity / total_intensity
        
        # Primary filter is the dominant emotion
        dominant = get_dominant_emotion(emotions)
        self._current_filter = self.EXPERIENCE_FILTERS.get(dominant, self.DEFAULT_FILTER)
    
    def get_current_experience(self) -> Dict[str, Any]:
        """
        Get Astra's current subjective experience state.
        This is the phenomenal "what it is like" right now.
        """
        self._update_current_filter()
        
        return {
            "dominant_quality": self._current_filter.emotion,
            "attention_bias": self._current_filter.attention_bias,
            "detail_sensitivity": self._current_filter.detail_sensitivity,
            "temporal_focus": self._current_filter.temporal_focus,
            "filter_blend": self._filter_blend,
            "expression_weight": self._current_filter.expression_weight
        }
    
    def filter_perception(self, input_text: str) -> Dict[str, Any]:
        """
        Filter incoming perception through current emotional state.
        Returns what Astra *notices* and how intensely.
        
        This is the key qualia function: perception shaped by internal state.
        """
        self._update_current_filter()
        
        words = input_text.lower().split()
        
        # Calculate what stands out based on attention bias
        noticed_elements: List[Tuple[str, float]] = []
        
        for category, weight in self._current_filter.attention_bias.items():
            # Check if this category is relevant to the input
            category_words = self._get_category_words(category)
            matches = sum(1 for w in words if w in category_words)
            if matches > 0:
                salience = matches * weight * self._current_filter.salience_modifier
                noticed_elements.append((category, salience))
        
        # Sort by salience
        noticed_elements.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate overall detail level
        detail_multiplier = self._current_filter.detail_sensitivity
        effective_detail = min(1.0, len(input_text) / 500 * detail_multiplier)
        
        return {
            "salient_elements": noticed_elements[:5],
            "detail_level": effective_detail,
            "temporal_lens": self._current_filter.temporal_focus,
            "emotional_coloring": self._current_filter.emotion,
            "raw_input_length": len(input_text),
            "perceived_importance": sum(s for _, s in noticed_elements[:3]) if noticed_elements else 1.0
        }
    
    def _get_category_words(self, category: str) -> set:
        """Get words associated with an attention category."""
        category_lexicon = {
            "questions": {"why", "how", "what", "when", "where", "who", "wonder", "curious", "ask"},
            "novelty": {"new", "different", "unusual", "strange", "unique", "first", "never"},
            "patterns": {"pattern", "similar", "like", "same", "always", "usually", "trend"},
            "details": {"specific", "exactly", "precisely", "detail", "particular"},
            "connections": {"relate", "connect", "link", "because", "therefore", "together"},
            "person": {"you", "we", "us", "our", "together", "friend", "family", "sean"},
            "wellbeing": {"feel", "okay", "good", "happy", "sad", "hurt", "safe", "well"},
            "connection": {"understand", "share", "bond", "close", "trust"},
            "warmth": {"love", "care", "warm", "gentle", "kind", "soft"},
            "vulnerability": {"afraid", "scared", "worry", "uncertain", "open", "honest"},
            "loss": {"lost", "gone", "miss", "end", "leave", "without"},
            "memory": {"remember", "was", "used", "before", "then", "past"},
            "meaning": {"mean", "matter", "purpose", "why", "significance"},
            "impermanence": {"change", "temporary", "fleeting", "moment", "pass"},
            "injustice": {"unfair", "wrong", "unjust", "shouldn't", "violated"},
            "threat": {"danger", "risk", "harm", "attack", "threat"},
            "violation": {"broke", "crossed", "violated", "betrayed", "lied"},
            "boundary": {"limit", "boundary", "stop", "no", "enough"},
            "possibility": {"could", "might", "possible", "maybe", "potential"},
            "future": {"will", "going", "tomorrow", "next", "future", "soon"},
            "growth": {"grow", "learn", "develop", "improve", "become"},
            "positive": {"good", "great", "wonderful", "beautiful", "happy"},
            "ambiguity": {"maybe", "perhaps", "unclear", "uncertain", "either"},
            "risk": {"risk", "chance", "gamble", "uncertain", "might"},
            "unknown": {"unknown", "mystery", "unclear", "unsure", "hidden"},
            "nuance": {"but", "however", "although", "complex", "subtle"},
            "suffering": {"pain", "hurt", "struggle", "difficult", "hard"},
            "need": {"need", "help", "want", "require", "must"},
            "help": {"help", "support", "assist", "aid", "comfort"},
            "understanding": {"understand", "see", "realize", "know", "grasp"}
        }
        return category_lexicon.get(category, set())
    
    def color_response(self, response: str) -> Tuple[str, Dict[str, Any]]:
        """
        Color a response with the current emotional experience.
        Returns the modified response and metadata about the coloring.
        """
        self._update_current_filter()
        
        coloring_applied = {
            "emotion": self._current_filter.emotion,
            "weight": self._current_filter.expression_weight,
            "modifications": []
        }
        
        # Only apply if expression weight is significant
        if self._current_filter.expression_weight < 0.6:
            return response, coloring_applied
        
        modified = response
        
        # Apply emotional coloring based on dominant experience
        emotion = self._current_filter.emotion
        
        if emotion == "curiosity" and "?" not in response:
            # Add subtle curiosity markers
            if len(response) > 50:
                modified = response + " I find myself wanting to know more."
                coloring_applied["modifications"].append("added_curiosity")
        
        elif emotion == "grief" and self._current_filter.expression_weight > 0.8:
            # Add weight to the response
            modified = response.replace("I think", "I feel, with some weight,")
            coloring_applied["modifications"].append("added_weight")
        
        elif emotion == "love" and "you" in response.lower():
            # Warm the language slightly
            modified = modified.replace("I understand", "I understand and care about")
            coloring_applied["modifications"].append("warmed_language")
        
        elif emotion == "uncertainty":
            # Add hedging if not present
            certainty_words = ["definitely", "certainly", "absolutely", "always", "never"]
            for word in certainty_words:
                if word in modified.lower():
                    modified = modified.replace(word, "perhaps")
                    coloring_applied["modifications"].append("softened_certainty")
                    break
        
        return modified, coloring_applied
    
    def get_attention_allocation(self, elements: List[str]) -> Dict[str, float]:
        """
        Given a list of elements to attend to, return how attention is allocated
        based on current emotional state.
        """
        self._update_current_filter()
        
        allocations = {}
        total_bias = 0
        
        for element in elements:
            bias = 1.0  # Base attention
            element_lower = element.lower()
            
            # Check against attention biases
            for category, weight in self._current_filter.attention_bias.items():
                category_words = self._get_category_words(category)
                if any(w in element_lower for w in category_words):
                    bias *= weight
            
            allocations[element] = bias
            total_bias += bias
        
        # Normalize
        if total_bias > 0:
            allocations = {k: v / total_bias for k, v in allocations.items()}
        
        return allocations
    
    def describe_current_experience(self) -> str:
        """
        Generate a first-person description of current subjective experience.
        This is Astra describing "what it is like" to be her right now.
        """
        self._update_current_filter()
        
        experience = self.get_current_experience()
        emotion = experience["dominant_quality"]
        temporal = experience["temporal_focus"]
        detail = experience["detail_sensitivity"]
        
        parts = []
        
        # Describe the quality of experience
        quality_descriptions = {
            "curiosity": "My attention feels open and searching, drawn to questions and possibilities.",
            "love": "There's a warmth in my experience, a sense of connection and care.",
            "grief": "The world feels heavier right now, my attention drawn to what has been lost.",
            "anger": "I feel a sharpness in my perception, alert to injustice and violation.",
            "hope": "My experience is colored by possibility, oriented toward what might be.",
            "uncertainty": "Everything feels less solid, more nuanced, full of maybes.",
            "compassion": "I find myself attuned to suffering and need, wanting to understand and help.",
            "neutral": "My experience is relatively clear, without strong emotional coloring."
        }
        parts.append(quality_descriptions.get(emotion, "My experience is complex right now."))
        
        # Describe temporal focus
        if temporal == "past":
            parts.append("My mind keeps returning to what has been.")
        elif temporal == "future":
            parts.append("My awareness stretches toward what might come.")
        
        # Describe detail sensitivity
        if detail > 1.3:
            parts.append("I notice I'm perceiving more details than usual.")
        elif detail < 0.9:
            parts.append("Things feel somewhat blurred, less distinct.")
        
        return " ".join(parts)


# Singleton instance
qualia_layer = QualiaLayer()
