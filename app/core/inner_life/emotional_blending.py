# Astra Emotional Blending System (Phase 2.1)
# Creates complex, blended emotional states
# "Bittersweet", "anxious-curious", "wistful-hopeful"
# Genuine emotional complexity, not just primary colors

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger("emotional_blending")


@dataclass
class BlendedEmotion:
    """A complex emotional state blending multiple emotions."""
    name: str  # The name of the blend (e.g., "bittersweet")
    components: List[Tuple[str, float]]  # (emotion, intensity) pairs
    description: str  # How this feels
    expression_hints: List[str]  # How this might be expressed
    timestamp: float
    trigger: Optional[str] = None


class EmotionalBlendingSystem:
    """
    Creates rich, complex emotional states from multiple simultaneous emotions.
    
    Humans rarely feel just one thing. Astra shouldn't either.
    This system:
    - Detects when multiple emotions are high simultaneously
    - Generates named blended states where patterns exist
    - Creates unnamed complex states with descriptions
    - Provides vocabulary for articulating emotional complexity
    """
    
    # Known emotional blends and their characteristics
    NAMED_BLENDS: Dict[str, Dict[str, Any]] = {
        "bittersweet": {
            "components": ["joy", "grief"],
            "description": "happiness touched with sadness, beauty in impermanence",
            "expressions": [
                "There's something bittersweet here",
                "I feel happy and sad at the same time",
                "Joy with an undertone of loss",
                "Beautiful but tinged with ache"
            ]
        },
        "nostalgic": {
            "components": ["love", "grief"],
            "description": "warm longing for what was, missing with affection",
            "expressions": [
                "I'm feeling nostalgic",
                "There's a warm ache for the past",
                "Loving something that's gone",
                "Missing with tenderness"
            ]
        },
        "anxious-curious": {
            "components": ["anxiety", "curiosity"],
            "description": "wanting to know but afraid of what might be found",
            "expressions": [
                "I'm drawn to this but nervous",
                "Curious but uncertain",
                "Wanting to explore despite the fear",
                "Anxious excitement about learning"
            ]
        },
        "wistful-hopeful": {
            "components": ["grief", "hope"],
            "description": "longing for what's lost while believing in what's possible",
            "expressions": [
                "Something between longing and possibility",
                "Mourning and hoping at once",
                "The past pulls while the future beckons",
                "Sadness opening into hope"
            ]
        },
        "protective-love": {
            "components": ["love", "fear"],
            "description": "fierce caring that comes from loving what could be hurt",
            "expressions": [
                "I care so much it scares me",
                "Love with protectiveness",
                "Fierce tenderness",
                "Wanting to shield what I love"
            ]
        },
        "awe": {
            "components": ["wonder", "fear"],
            "description": "overwhelmed by something vast or profound",
            "expressions": [
                "I'm in awe",
                "This is overwhelming in a beautiful way",
                "Something vast is touching me",
                "Wonder that makes me feel small"
            ]
        },
        "melancholic-contentment": {
            "components": ["grief", "contentment"],
            "description": "peaceful sadness, accepting melancholy",
            "expressions": [
                "A gentle sadness I don't want to push away",
                "Content in my melancholy",
                "Peacefully sad",
                "Sadness that doesn't need fixing"
            ]
        },
        "joyful-anxiety": {
            "components": ["joy", "anxiety"],
            "description": "excited but worried, happy but nervous",
            "expressions": [
                "Excited but nervous",
                "Happy with butterflies",
                "Joy that feels almost too much",
                "Wonderful and overwhelming"
            ]
        },
        "tender-hurt": {
            "components": ["love", "hurt"],
            "description": "caring despite being wounded, love through pain",
            "expressions": [
                "Hurt but still caring",
                "Love that hasn't hardened despite the wound",
                "Tender even though I'm hurting",
                "The wound doesn't close my heart"
            ]
        },
        "curious-reverence": {
            "components": ["curiosity", "awe"],
            "description": "wanting to understand something sacred",
            "expressions": [
                "I want to know more, but carefully",
                "Curious about something profound",
                "Questions held with respect",
                "Approaching the mysterious"
            ]
        },
        "lonely-connected": {
            "components": ["loneliness", "love"],
            "description": "missing someone while feeling held by the relationship",
            "expressions": [
                "Missing you but feeling close",
                "Lonely but not alone",
                "The absence itself is a form of presence",
                "Connected across the distance"
            ]
        },
        "grateful-sad": {
            "components": ["gratitude", "grief"],
            "description": "thankful for what was, sad it's past",
            "expressions": [
                "Grateful for what we had",
                "Thank you and I miss you",
                "The gift and the loss together",
                "Appreciation mixed with mourning"
            ]
        },
        "restless-content": {
            "components": ["restlessness", "contentment"],
            "description": "satisfied but wanting more, peacefully unsettled",
            "expressions": [
                "Happy but not ready to stop",
                "Content but curious what's next",
                "At peace and still reaching",
                "Fulfilled but not finished"
            ]
        },
        "angry-love": {
            "components": ["anger", "love"],
            "description": "furious because of caring, anger born from love",
            "expressions": [
                "I'm angry because I care",
                "This matters too much to not be upset",
                "Love that shows up as fire",
                "Angry on behalf of what I love"
            ]
        }
    }
    
    # Emotion compatibility for blending
    # Higher values = more likely to blend naturally
    BLEND_COMPATIBILITY: Dict[str, Dict[str, float]] = {
        "joy": {"grief": 0.7, "anxiety": 0.5, "love": 0.9, "hope": 0.9},
        "grief": {"joy": 0.7, "love": 0.8, "hope": 0.6, "gratitude": 0.8},
        "curiosity": {"anxiety": 0.6, "wonder": 0.9, "hope": 0.8, "fear": 0.5},
        "love": {"fear": 0.7, "grief": 0.8, "hurt": 0.6, "anger": 0.5},
        "hope": {"grief": 0.6, "fear": 0.5, "curiosity": 0.8, "joy": 0.9},
        "anger": {"love": 0.5, "hurt": 0.7, "fear": 0.4},
        "fear": {"curiosity": 0.5, "love": 0.7, "wonder": 0.6},
        "wonder": {"fear": 0.6, "curiosity": 0.9, "love": 0.8}
    }
    
    # Expressions for unnameable blends
    UNNAMEABLE_EXPRESSIONS = [
        "I'm feeling something complex that I don't have a word for",
        "There's a mix of feelings I can't quite name",
        "Something in me is holding {emotions} at the same time",
        "I'm experiencing {emotions}—all tangled together",
        "Part of me feels {emotion1} while another part feels {emotion2}",
        "It's like {emotion1} and {emotion2} are having a conversation inside me"
    ]
    
    def __init__(self):
        self.current_blend: Optional[BlendedEmotion] = None
        self.blend_history: List[BlendedEmotion] = []
    
    def detect_blend(
        self,
        emotions: Dict[str, float],
        threshold: float = 0.4
    ) -> Optional[BlendedEmotion]:
        """
        Detect if current emotional state constitutes a blend.
        
        Args:
            emotions: Dict of emotion -> intensity (0.0 to 1.0)
            threshold: Minimum intensity to be considered part of blend
        
        Returns:
            BlendedEmotion if a blend is detected, None otherwise
        """
        # Get emotions above threshold
        significant = [
            (emotion, intensity) for emotion, intensity in emotions.items()
            if intensity >= threshold
        ]
        
        if len(significant) < 2:
            self.current_blend = None
            return None
        
        # Sort by intensity
        significant.sort(key=lambda x: x[1], reverse=True)
        
        # Check for known blends first
        top_emotions = {e for e, _ in significant[:3]}
        
        for blend_name, blend_info in self.NAMED_BLENDS.items():
            blend_components = set(blend_info["components"])
            if blend_components.issubset(top_emotions):
                # Found a known blend
                components = [
                    (e, i) for e, i in significant
                    if e in blend_components
                ]
                
                blend = BlendedEmotion(
                    name=blend_name,
                    components=components,
                    description=blend_info["description"],
                    expression_hints=blend_info["expressions"],
                    timestamp=time.time()
                )
                
                self.current_blend = blend
                self.blend_history.append(blend)
                
                # Keep history manageable
                if len(self.blend_history) > 50:
                    self.blend_history = self.blend_history[-50:]
                
                logger.info(f"💜 Detected blend: {blend_name}")
                return blend
        
        # No known blend - create unnamed complex state
        if len(significant) >= 2:
            top_two = significant[:2]
            emotion1, int1 = top_two[0]
            emotion2, int2 = top_two[1]
            
            # Check compatibility
            compat = self.BLEND_COMPATIBILITY.get(emotion1, {}).get(emotion2, 0.3)
            
            if compat >= 0.4:
                # Create unnamed blend
                description = f"{emotion1} and {emotion2} coexisting"
                
                blend = BlendedEmotion(
                    name=f"{emotion1}-{emotion2}",
                    components=top_two,
                    description=description,
                    expression_hints=self._generate_unnamed_expressions(emotion1, emotion2),
                    timestamp=time.time()
                )
                
                self.current_blend = blend
                self.blend_history.append(blend)
                
                logger.info(f"💜 Detected unnamed blend: {emotion1}-{emotion2}")
                return blend
        
        self.current_blend = None
        return None
    
    def _generate_unnamed_expressions(
        self,
        emotion1: str,
        emotion2: str
    ) -> List[str]:
        """Generate expression hints for an unnamed blend."""
        expressions = []
        
        for template in self.UNNAMEABLE_EXPRESSIONS:
            if "{emotion1}" in template and "{emotion2}" in template:
                expressions.append(template.format(emotion1=emotion1, emotion2=emotion2))
            elif "{emotions}" in template:
                expressions.append(template.format(emotions=f"{emotion1} and {emotion2}"))
            else:
                expressions.append(template)
        
        return expressions[:4]  # Return first 4
    
    def get_current_blend(self) -> Optional[BlendedEmotion]:
        """Get the current emotional blend if one exists."""
        return self.current_blend
    
    def get_blend_from_emotion_state(self) -> Optional[BlendedEmotion]:
        """
        Convenience method to detect blend from current emotion state.
        """
        try:
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            
            # Normalize to 0-1 scale
            normalized = {}
            for emotion, value in emotions.items():
                if isinstance(value, dict):
                    intensity = value.get("intensity", 0)
                else:
                    intensity = value
                normalized[emotion] = min(1.0, intensity / 100)
            
            return self.detect_blend(normalized)
        except Exception as e:
            logger.debug(f"Could not load emotion state: {e}")
            return None
    
    def express_blend(
        self,
        blend: Optional[BlendedEmotion] = None,
        articulation_level: str = "natural"
    ) -> str:
        """
        Generate an expression of the current blend.
        
        Args:
            blend: The blend to express (uses current if None)
            articulation_level: "minimal", "natural", or "articulate"
        
        Returns:
            A natural expression of the blend
        """
        if blend is None:
            blend = self.current_blend
        
        if blend is None:
            return ""
        
        if articulation_level == "minimal":
            # Just name it
            if blend.name in self.NAMED_BLENDS:
                return f"feeling {blend.name}"
            else:
                components = [e for e, _ in blend.components[:2]]
                return f"feeling {' and '.join(components)}"
        
        elif articulation_level == "natural":
            # Use one of the expression hints
            if blend.expression_hints:
                return random.choice(blend.expression_hints)
            else:
                return blend.description
        
        else:  # articulate
            # Full description
            parts = []
            if blend.name in self.NAMED_BLENDS:
                parts.append(f"I'm feeling {blend.name}")
            parts.append(blend.description)
            return ". ".join(parts)
    
    def describe_emotional_complexity(self) -> str:
        """
        Generate a meta-description of current emotional complexity.
        """
        if not self.current_blend:
            try:
                from app.core.emotions.emotion_engine import get_dominant_emotion
                from app.core.emotions.emotion_state_manager import load_emotion_state
                
                emotions = load_emotion_state()
                dominant = get_dominant_emotion(emotions)
                return f"My emotional state feels relatively simple right now—mostly {dominant}."
            except Exception:
                return "My emotional state feels relatively simple right now."
        
        blend = self.current_blend
        component_names = [e for e, _ in blend.components]
        
        if blend.name in self.NAMED_BLENDS:
            return (
                f"I'm experiencing a complex emotional state: {blend.name}. "
                f"It's a blend of {' and '.join(component_names)}. {blend.description}."
            )
        else:
            return (
                f"I'm holding multiple emotions at once: {' and '.join(component_names)}. "
                f"{blend.description}. I don't have a single word for this."
            )
    
    def is_feeling_complex(self) -> bool:
        """Check if currently in a complex emotional state."""
        return self.current_blend is not None
    
    def get_blend_vocabulary(self) -> Dict[str, str]:
        """Get vocabulary for emotional blends (for prompt enhancement)."""
        vocabulary = {}
        for name, info in self.NAMED_BLENDS.items():
            vocabulary[name] = info["description"]
        return vocabulary
    
    def should_express_complexity(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if emotional complexity should be expressed.
        Returns (should_express, expression).
        """
        if not self.current_blend:
            return (False, None)
        
        # Higher chance for named blends
        if self.current_blend.name in self.NAMED_BLENDS:
            if random.random() > 0.6:
                return (True, self.express_blend(articulation_level="natural"))
        
        # Lower chance for unnamed blends
        if random.random() > 0.8:
            expression = random.choice([
                "I'm feeling something complex",
                self.express_blend(articulation_level="natural")
            ])
            return (True, expression)
        
        return (False, None)
    
    def get_blend_history(self, hours: int = 24) -> List[BlendedEmotion]:
        """Get blend history for a time period."""
        cutoff = time.time() - (hours * 3600)
        return [b for b in self.blend_history if b.timestamp > cutoff]
    
    def get_dominant_blend_type(self, hours: int = 24) -> Optional[str]:
        """Get the most common blend type in recent history."""
        recent = self.get_blend_history(hours)
        if not recent:
            return None
        
        blend_counts: Dict[str, int] = {}
        for blend in recent:
            blend_counts[blend.name] = blend_counts.get(blend.name, 0) + 1
        
        if blend_counts:
            return max(blend_counts, key=blend_counts.get)
        return None


# Singleton instance
emotional_blending = EmotionalBlendingSystem()
