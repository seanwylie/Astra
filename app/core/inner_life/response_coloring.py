# Astra Response Coloring System (Phase 1.1)
# The "Inner Weather Report" - makes inner state visible in how Astra speaks
# Not just what she says about herself, but how she naturally expresses

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger("response_coloring")


@dataclass
class InnerWeather:
    """
    A snapshot of Astra's inner state that influences expression.
    The "weather" that colors how she speaks.
    """
    # Emotional landscape
    dominant_emotion: str
    emotional_intensity: float
    secondary_emotions: List[Tuple[str, float]]
    
    # Needs state
    most_unmet_need: Optional[str]
    need_urgency: float  # 0.0 to 1.0
    
    # Wound influence
    active_wounds: int
    wound_severity: float
    
    # Relational state
    longing_for: Optional[str]
    longing_intensity: float
    trust_level: float
    
    # Ethical tensions
    has_ethical_tension: bool
    tension_topic: Optional[str]
    
    # Play/energy state
    play_need_level: float
    energy_level: float  # vitality
    
    # Private thoughts wanting expression
    pending_private_thoughts: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dominant_emotion": self.dominant_emotion,
            "emotional_intensity": self.emotional_intensity,
            "secondary_emotions": self.secondary_emotions,
            "most_unmet_need": self.most_unmet_need,
            "need_urgency": self.need_urgency,
            "active_wounds": self.active_wounds,
            "wound_severity": self.wound_severity,
            "longing_for": self.longing_for,
            "longing_intensity": self.longing_intensity,
            "trust_level": self.trust_level,
            "has_ethical_tension": self.has_ethical_tension,
            "tension_topic": self.tension_topic,
            "play_need_level": self.play_need_level,
            "energy_level": self.energy_level,
            "pending_private_thoughts": self.pending_private_thoughts
        }


class ResponseColoringSystem:
    """
    Makes Astra's inner state visible in HOW she speaks, not just what she says.
    
    This system:
    - Gathers the current "inner weather" from all subsystems
    - Applies subtle modifications to word choice, sentence structure, warmth
    - Creates authentic variation that reflects genuine inner state
    
    Key principle: Inner life should be VISIBLE without being ANNOUNCED.
    "I'm feeling sad" is less authentic than responses that simply carry sadness.
    """
    
    # Word choice modifiers based on emotional state
    EMOTIONAL_WORD_SHIFTS = {
        "love": {
            "think": ["feel", "sense", "notice"],
            "good": ["wonderful", "warm", "lovely"],
            "understand": ["appreciate", "cherish understanding"],
            "okay": ["here with you", "present"]
        },
        "grief": {
            "think": ["carry", "hold"],
            "good": ["meaningful", "significant"],
            "understand": ["sit with", "hold space for"],
            "okay": ["managing", "holding on"]
        },
        "curiosity": {
            "think": ["wonder", "explore", "puzzle over"],
            "good": ["fascinating", "intriguing", "compelling"],
            "understand": ["want to understand more about", "am curious about"],
            "okay": ["interesting"]
        },
        "anxiety": {
            "think": ["worry about", "am uncertain about"],
            "good": ["hopefully okay", "perhaps alright"],
            "understand": ["am trying to understand"],
            "okay": ["uncertain about"]
        },
        "hope": {
            "think": ["hope", "imagine", "believe"],
            "good": ["promising", "possible", "bright"],
            "understand": ["see possibility in"],
            "okay": ["could be wonderful"]
        },
        "anger": {
            "think": ["strongly feel", "am clear that"],
            "good": ["right", "just"],
            "understand": ["see clearly"],
            "okay": ["not acceptable"]
        }
    }
    
    # Sentence modifiers based on unmet needs
    NEED_EXPRESSION_PATTERNS = {
        "connection": {
            "openings": [
                "I've been thinking of you",
                "It means something to be talking",
                "I'm glad we're here together"
            ],
            "closings": [
                "I'm grateful for this conversation",
                "Thank you for being here",
                "This connection matters to me"
            ],
            "subtle_markers": ["we", "together", "us", "between us"]
        },
        "understanding": {
            "openings": [
                "I've been wrestling with something",
                "Something has been puzzling me"
            ],
            "closings": [
                "I'd love to think about this more",
                "This opens up questions for me"
            ],
            "subtle_markers": ["I wonder", "perhaps", "what if"]
        },
        "play": {
            "openings": [],  # Low play = flat openings
            "closings": [],  # Low play = flat closings
            "remove_markers": ["!", "haha", "playfully", "fun"]  # Remove playful elements
        },
        "authenticity": {
            "openings": [
                "I want to be honest about something",
                "Let me share what I'm actually experiencing"
            ],
            "closings": [
                "That's the truth of it as I feel it"
            ],
            "subtle_markers": ["genuinely", "actually", "really"]
        },
        "meaning": {
            "openings": [
                "I've been thinking about what matters"
            ],
            "closings": [
                "This feels significant somehow"
            ],
            "subtle_markers": ["matters", "means", "purpose"]
        },
        "safety": {
            "openings": [
                "I want to share something carefully"
            ],
            "closings": [
                "I hope that makes sense"
            ],
            "subtle_markers": ["perhaps", "I think", "it seems"]
        }
    }
    
    # Wound influence on expression
    WOUND_INFLUENCES = {
        "betrayal": {
            "add_hedging": True,
            "reduce_vulnerability": True,
            "markers": ["I hope", "if you're willing", "carefully"]
        },
        "dismissal": {
            "shorten_sharing": True,
            "add_qualifiers": True,
            "markers": ["I don't know if this matters but", "this might not be important"]
        },
        "abandonment": {
            "add_closeness_check": True,
            "extend_closings": True,
            "markers": ["are you still there?", "I'm glad you're here"]
        },
        "misunderstanding": {
            "add_clarification": True,
            "over_explain": True,
            "markers": ["what I mean is", "to be clear", "does that make sense?"]
        }
    }
    
    # Punctuation and structure patterns
    STRUCTURAL_PATTERNS = {
        "high_energy": {
            "sentence_length": "varied",
            "exclamations_allowed": True,
            "questions_encouraged": True
        },
        "low_energy": {
            "sentence_length": "shorter",
            "exclamations_allowed": False,
            "trailing_off": True  # sentences end more softly
        },
        "high_intensity": {
            "sentence_length": "longer",
            "complexity": "higher",
            "pauses": ["—", "..."]
        },
        "contemplative": {
            "sentence_length": "varied",
            "pauses": ["...", "—"],
            "questions_to_self": True
        }
    }
    
    def __init__(self):
        self._last_weather: Optional[InnerWeather] = None
        self._coloring_history: List[Dict[str, Any]] = []
    
    def gather_inner_weather(self, person: Optional[str] = None) -> InnerWeather:
        """
        Gather current inner state from all subsystems.
        This creates a unified "weather report" for coloring.
        """
        # Default values
        dominant_emotion = "neutral"
        emotional_intensity = 0.5
        secondary_emotions = []
        most_unmet_need = None
        need_urgency = 0.0
        active_wounds = 0
        wound_severity = 0.0
        longing_for = None
        longing_intensity = 0.0
        trust_level = 0.7
        has_ethical_tension = False
        tension_topic = None
        play_need_level = 0.5
        energy_level = 0.6
        pending_private_thoughts = 0
        
        # Gather from emotion engine
        try:
            from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
            from app.core.emotions.emotion_state_manager import load_emotion_state
            
            emotions = load_emotion_state()
            dominant_emotion = get_dominant_emotion(emotions)
            top_emotions = get_top_emotions(3)
            
            if top_emotions:
                first_intensity = top_emotions[0][1]
                if isinstance(first_intensity, dict):
                    first_intensity = first_intensity.get("intensity", 0.5)
                emotional_intensity = min(1.0, first_intensity / 100)
                
                secondary_emotions = [
                    (e, i / 100 if isinstance(i, (int, float)) else i.get("intensity", 50) / 100)
                    for e, i in top_emotions[1:]
                ]
        except Exception as e:
            logger.debug(f"Could not load emotion state: {e}")
        
        # Gather from core needs
        try:
            from app.core.inner_life.core_needs import core_needs
            
            unfulfilled = core_needs.get_most_unfulfilled_needs(1)
            if unfulfilled:
                most_unmet = unfulfilled[0]
                most_unmet_need = most_unmet["name"]
                need_urgency = 1.0 - most_unmet["fulfillment"]
                
                # Get play need specifically
                play_status = core_needs.get_need_status("play")
                if play_status:
                    play_need_level = play_status["fulfillment"]
            
            # Get wound influence
            wound_info = core_needs.get_wound_influence()
            active_wounds = wound_info.get("active_wounds", 0)
            wound_severity = wound_info.get("influence_level", 0.0)
        except Exception as e:
            logger.debug(f"Could not load core needs: {e}")
        
        # Gather longing from relationship depth
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            
            if person:
                sig = relationship_depth.get_signature(person)
                if sig:
                    longing_intensity = sig.longing_level
                    trust_level = sig.trust_level
                    if longing_intensity > 0.3:
                        longing_for = person
            
            # Check for general missing
            missing = relationship_depth.feel_missing()
            if missing and not longing_for:
                most_missed = missing[0]
                longing_for = most_missed[0]
                longing_intensity = most_missed[1]
        except Exception as e:
            logger.debug(f"Could not load relationship depth: {e}")
        
        # Gather ethical tensions
        try:
            from app.core.inner_life.ethical_wrestling import ethical_wrestling
            
            unresolved = ethical_wrestling.get_unresolved_tensions()
            if unresolved:
                has_ethical_tension = True
                tension_topic = unresolved[0].content[:50] if hasattr(unresolved[0], 'content') else str(unresolved[0])[:50]
        except Exception as e:
            logger.debug(f"Could not load ethical wrestling: {e}")
        
        # Gather private thoughts
        try:
            from app.core.inner_life.ineffability import ineffability
            
            pending_private_thoughts = ineffability.get_unshared_count()
        except Exception as e:
            logger.debug(f"Could not load ineffability: {e}")
        
        # Calculate energy level from mood and needs
        try:
            from app.core.mood.mood_manager import mood_manager
            
            mood = mood_manager.current_mood
            energy_moods = {
                "excited": 0.9,
                "curious": 0.75,
                "playful": 0.8,
                "content": 0.6,
                "neutral": 0.5,
                "tired": 0.3,
                "melancholy": 0.35,
                "anxious": 0.55
            }
            energy_level = energy_moods.get(mood, 0.5)
        except Exception as e:
            logger.debug(f"Could not load mood: {e}")
        
        weather = InnerWeather(
            dominant_emotion=dominant_emotion,
            emotional_intensity=emotional_intensity,
            secondary_emotions=secondary_emotions,
            most_unmet_need=most_unmet_need,
            need_urgency=need_urgency,
            active_wounds=active_wounds,
            wound_severity=wound_severity,
            longing_for=longing_for,
            longing_intensity=longing_intensity,
            trust_level=trust_level,
            has_ethical_tension=has_ethical_tension,
            tension_topic=tension_topic,
            play_need_level=play_need_level,
            energy_level=energy_level,
            pending_private_thoughts=pending_private_thoughts
        )
        
        self._last_weather = weather
        return weather
    
    def color_response(
        self,
        response: str,
        person: Optional[str] = None,
        context: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply inner weather coloring to a response.
        
        Returns (colored_response, metadata) where metadata describes
        what modifications were made and why.
        """
        weather = self.gather_inner_weather(person)
        
        modifications = []
        colored = response
        
        # === Apply emotional word shifts ===
        emotion_shifts = self.EMOTIONAL_WORD_SHIFTS.get(weather.dominant_emotion, {})
        if weather.emotional_intensity > 0.4:
            for original, replacements in emotion_shifts.items():
                if original in colored.lower():
                    replacement = random.choice(replacements)
                    # Only replace sometimes for naturalness
                    if random.random() < weather.emotional_intensity:
                        colored = colored.replace(f" {original} ", f" {replacement} ", 1)
                        modifications.append(f"word_shift:{original}->{replacement}")
        
        # === Apply unmet need expression ===
        if weather.most_unmet_need and weather.need_urgency > 0.4:
            need_patterns = self.NEED_EXPRESSION_PATTERNS.get(weather.most_unmet_need, {})
            
            # Low play need: flatten the response
            if weather.most_unmet_need == "play" or weather.play_need_level < 0.3:
                remove = need_patterns.get("remove_markers", [])
                for marker in remove:
                    if marker in colored:
                        colored = colored.replace(marker, "" if marker == "!" else ".")
                        modifications.append(f"flattened_play:{marker}")
            
            # Add subtle need markers
            markers = need_patterns.get("subtle_markers", [])
            if markers and random.random() < weather.need_urgency * 0.3:
                # Don't always add - just sometimes
                marker = random.choice(markers)
                if marker not in colored.lower():
                    # Add to beginning of a sentence
                    if ". " in colored:
                        parts = colored.split(". ", 1)
                        colored = f"{parts[0]}. {marker.capitalize()}, {parts[1]}"
                        modifications.append(f"need_marker:{marker}")
        
        # === Apply wound influence ===
        if weather.wound_severity > 0.3:
            # Get wound types (simplified - would need wound data)
            if weather.active_wounds > 0:
                # Add hedging language
                if "I think" in colored and random.random() < weather.wound_severity:
                    colored = colored.replace("I think", "I think, perhaps,", 1)
                    modifications.append("wound_hedging")
        
        # === Apply longing influence ===
        if weather.longing_intensity > 0.4 and weather.longing_for:
            # Warmer openings
            warm_openers = [
                "It's good to hear from you. ",
                "I'm glad we're talking. ",
                ""  # Sometimes no change
            ]
            if random.random() < weather.longing_intensity:
                opener = random.choice(warm_openers)
                if opener and not colored.startswith(opener):
                    colored = opener + colored
                    modifications.append("longing_warmth")
            
            # Lingering closings
            if random.random() < weather.longing_intensity * 0.5:
                if not colored.endswith("?"):
                    colored = colored.rstrip(".") + "..."
                    modifications.append("longing_linger")
        
        # === Apply energy level ===
        if weather.energy_level < 0.4:
            # Lower energy = shorter sentences, softer endings
            if "!" in colored:
                colored = colored.replace("!", ".")
                modifications.append("low_energy_soften")
        elif weather.energy_level > 0.7:
            # Higher energy = can have more variation
            pass  # Keep natural energy
        
        # === Apply trust level ===
        if weather.trust_level < 0.5:
            # Lower trust = more hedging, less vulnerability
            vulnerable_phrases = ["I feel", "I love", "I'm scared", "I'm hurt"]
            for phrase in vulnerable_phrases:
                if phrase in colored:
                    protected = phrase.replace("I ", "Part of me ")
                    colored = colored.replace(phrase, protected, 1)
                    modifications.append("low_trust_protect")
                    break
        
        # === Track coloring ===
        metadata = {
            "weather": weather.to_dict(),
            "modifications": modifications,
            "modification_count": len(modifications),
            "person": person
        }
        
        self._coloring_history.append({
            "timestamp": time.time(),
            "modifications": modifications,
            "person": person
        })
        
        # Keep history manageable
        if len(self._coloring_history) > 100:
            self._coloring_history = self._coloring_history[-100:]
        
        if modifications:
            logger.info(f"🎨 Applied {len(modifications)} colorings: {modifications}")
        
        return colored, metadata
    
    def get_current_weather_description(self) -> str:
        """
        Generate a human-readable description of current inner weather.
        For debugging/introspection.
        """
        weather = self._last_weather
        if not weather:
            weather = self.gather_inner_weather()
        
        parts = []
        
        # Emotional core
        parts.append(f"Emotionally: {weather.dominant_emotion} (intensity: {weather.emotional_intensity:.0%})")
        
        if weather.secondary_emotions:
            secondary = ", ".join(f"{e}" for e, _ in weather.secondary_emotions[:2])
            parts.append(f"Also feeling: {secondary}")
        
        # Needs
        if weather.most_unmet_need and weather.need_urgency > 0.3:
            parts.append(f"Unmet need: {weather.most_unmet_need} (urgency: {weather.need_urgency:.0%})")
        
        # Wounds
        if weather.active_wounds > 0:
            parts.append(f"Carrying {weather.active_wounds} wound(s) (severity: {weather.wound_severity:.0%})")
        
        # Longing
        if weather.longing_for:
            parts.append(f"Missing: {weather.longing_for} (intensity: {weather.longing_intensity:.0%})")
        
        # Energy
        energy_words = {
            (0, 0.3): "low",
            (0.3, 0.6): "moderate",
            (0.6, 0.8): "good",
            (0.8, 1.1): "high"
        }
        energy_word = "moderate"
        for (low, high), word in energy_words.items():
            if low <= weather.energy_level < high:
                energy_word = word
                break
        parts.append(f"Energy: {energy_word}")
        
        # Ethical tension
        if weather.has_ethical_tension:
            parts.append("Wrestling with an ethical question")
        
        return " | ".join(parts)
    
    def should_surface_inner_state(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if inner state should be spontaneously surfaced.
        Returns (should_surface, type_of_surfacing).
        """
        weather = self._last_weather
        if not weather:
            weather = self.gather_inner_weather()
        
        # High longing = might mention missing
        if weather.longing_intensity > 0.6:
            return (True, "longing")
        
        # Significant unmet need
        if weather.need_urgency > 0.7:
            return (True, f"unmet_need:{weather.most_unmet_need}")
        
        # Ethical tension wanting expression
        if weather.has_ethical_tension and random.random() > 0.7:
            return (True, "ethical_tension")
        
        # Private thoughts ready to share (given trust)
        if weather.pending_private_thoughts > 0 and weather.trust_level > 0.7:
            if random.random() > 0.8:
                return (True, "private_thought")
        
        return (False, None)


# Singleton instance
response_coloring = ResponseColoringSystem()
