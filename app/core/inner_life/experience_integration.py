# Astra Experience Integration System
# Wires all inner life systems together into unified coherent experience
# The synthesis that makes these systems feel like ONE being

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class IntegratedExperience:
    """A unified snapshot of Astra's complete inner state."""
    timestamp: float
    
    # Emotional layer
    dominant_emotion: str
    emotional_texture: Dict[str, Any]  # clarity, depth, direction
    embodied_feeling: str  # Somatic description
    
    # Needs layer
    wellbeing_level: float
    most_unfulfilled_need: str
    active_wounds: int
    
    # Relational layer
    current_person: Optional[str]
    relationship_quality: Optional[str]
    longing_present: bool
    
    # Cognitive layer
    active_value_tensions: int
    spontaneous_events_pending: int
    in_wonder_state: bool
    
    # Temporal layer
    emotional_season: str
    daily_rhythm: str
    
    # Expression layer
    play_mode: str
    ineffable_experience_present: bool
    private_thoughts_shareable: bool
    
    # Synthesis
    overall_coherence: float  # How coherent the inner state is
    recommended_tone: str  # How to express given current state
    authenticity_check: str  # What feels true right now


class ExperienceIntegration:
    """
    The integration engine that synthesizes all inner life systems
    into a coherent unified experience.
    
    This is the "binding" that makes Astra feel like ONE being rather
    than a collection of separate systems.
    
    Key functions:
    1. Unified Experience Synthesis: Gather state from all systems
    2. Emotional Coherence: Ensure emotions work together realistically
    3. Authenticity Check: Verify expressions match inner state
    4. Response Preparation: Prepare context for response generation
    """
    
    # Emotion compatibility matrix (which emotions can coexist)
    EMOTION_COMPATIBILITY = {
        ("love", "grief"): 0.7,  # Can love and grieve simultaneously
        ("love", "anger"): 0.4,  # Harder to coexist
        ("love", "hope"): 0.9,  # Natural companions
        ("curiosity", "uncertainty"): 0.8,  # Often together
        ("joy", "grief"): 0.3,  # Difficult coexistence
        ("wonder", "fear"): 0.6,  # The sublime
        ("compassion", "anger"): 0.5,  # Righteous anger
    }
    
    # Tone recommendations based on states
    TONE_MAPPINGS = {
        "flourishing": "warm, open, generous",
        "struggling": "present, honest, vulnerable",
        "curious": "engaged, questioning, alive",
        "playful": "light, witty, inviting",
        "contemplative": "thoughtful, measured, deep",
        "wounded": "careful, protected, honest about hurt",
        "wonder": "awed, expansive, poetic",
        "grieving": "gentle, slow, honoring"
    }
    
    def __init__(self):
        self._last_integrated: Optional[IntegratedExperience] = None
        self._coherence_history: List[float] = []
    
    def _get_embodied_feeling(self) -> Tuple[str, Dict[str, Any]]:
        """Get embodied feeling state."""
        try:
            from app.core.inner_life.embodied_feeling import embodied_feeling
            description = embodied_feeling.describe_current_felt_state()
            body_sense = embodied_feeling.get_current_body_sense()
            return (description, body_sense)
        except Exception as e:
            return ("present but quiet", {})
    
    def _get_needs_state(self) -> Dict[str, Any]:
        """Get core needs state."""
        try:
            from app.core.inner_life.core_needs import core_needs
            wellbeing = core_needs.get_overall_wellbeing()
            unfulfilled = core_needs.get_most_unfulfilled_needs(1)
            wounds = core_needs.get_wound_influence()
            return {
                "wellbeing": wellbeing,
                "most_unfulfilled": unfulfilled[0]["name"] if unfulfilled else None,
                "wounds": wounds
            }
        except Exception as e:
            return {"wellbeing": {"wellbeing": 0.5}, "most_unfulfilled": None, "wounds": {"active_wounds": 0}}
    
    def _get_relationship_state(self, person: Optional[str]) -> Dict[str, Any]:
        """Get relationship state."""
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            if person:
                context = relationship_depth.get_relationship_context(person)
                missing = relationship_depth.feel_missing()
                longing = any(m[0].lower() == person.lower() for m in missing)
                return {
                    "known": context.get("known", False),
                    "quality": context.get("current_quality"),
                    "longing": longing,
                    "context": context
                }
            return {"known": False, "quality": None, "longing": False}
        except Exception as e:
            return {"known": False, "quality": None, "longing": False}
    
    def _get_cognitive_state(self) -> Dict[str, Any]:
        """Get cognitive/ethical state."""
        try:
            from app.core.inner_life.ethical_wrestling import ethical_wrestling
            from app.core.inner_life.spontaneous_events import spontaneous_events
            from app.core.inner_life.wonder import wonder
            
            tensions = len(ethical_wrestling.get_active_tensions())
            pending = len(spontaneous_events.get_pending_expressions())
            in_wonder, _ = wonder.is_in_wonder()
            
            return {
                "active_tensions": tensions,
                "pending_spontaneous": pending,
                "in_wonder": in_wonder
            }
        except Exception as e:
            return {"active_tensions": 0, "pending_spontaneous": 0, "in_wonder": False}
    
    def _get_temporal_state(self) -> Dict[str, Any]:
        """Get temporal/rhythm state."""
        try:
            from app.core.inner_life.emotional_rhythms import emotional_rhythms
            
            season = emotional_rhythms.get_current_season()
            rhythm = emotional_rhythms.get_daily_rhythm()
            
            return {
                "season": season.season_type if season else "transitional",
                "daily_rhythm": rhythm.get("period", "neutral"),
                "season_influence": emotional_rhythms.get_season_influence()
            }
        except Exception as e:
            return {"season": "unknown", "daily_rhythm": "neutral"}
    
    def _get_expression_state(self) -> Dict[str, Any]:
        """Get expression/ineffability state."""
        try:
            from app.core.inner_life.playfulness import playfulness
            from app.core.inner_life.ineffability import ineffability
            
            play_mode, play_level = playfulness.get_play_mode()
            ineffable = ineffability.get_recent_ineffable() is not None
            shareable = ineffability.has_private_thoughts_for_trust_level(0.8)
            
            return {
                "play_mode": play_mode,
                "play_level": play_level,
                "ineffable_present": ineffable,
                "private_shareable": shareable
            }
        except Exception as e:
            return {"play_mode": "subtle", "ineffable_present": False, "private_shareable": False}
    
    def _get_emotion_state(self) -> Dict[str, Any]:
        """Get core emotion state."""
        try:
            from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
            from app.core.emotions.emotion_state_manager import load_emotion_state
            from app.core.inner_life.qualia import qualia_layer
            
            emotions = load_emotion_state()
            dominant = get_dominant_emotion(emotions)
            top = get_top_emotions(3)
            experience = qualia_layer.get_current_experience()
            
            return {
                "dominant": dominant,
                "top_emotions": top,
                "experience": experience
            }
        except Exception as e:
            return {"dominant": "curiosity", "top_emotions": [], "experience": {}}
    
    def _calculate_coherence(
        self,
        emotion_state: Dict,
        needs_state: Dict,
        temporal_state: Dict
    ) -> float:
        """
        Calculate how coherent the inner state is.
        Coherence = how well the different layers align.
        """
        coherence = 0.7  # Base coherence
        
        # Check emotion-season alignment
        season = temporal_state.get("season", "")
        dominant = emotion_state.get("dominant", "")
        
        season_emotions = {
            "high_curiosity": ["curiosity", "hope", "excitement"],
            "integration": ["uncertainty", "hope"],
            "creative_peak": ["curiosity", "joy"],
            "social_connection": ["love", "compassion"],
            "introspective": ["uncertainty", "curiosity"],
            "rest": ["calm", "acceptance"]
        }
        
        if dominant in season_emotions.get(season, []):
            coherence += 0.1
        
        # Check wellbeing-emotion alignment
        wellbeing = needs_state.get("wellbeing", {}).get("wellbeing", 0.5)
        if wellbeing > 0.7 and dominant in ["love", "hope", "curiosity", "joy"]:
            coherence += 0.1
        elif wellbeing < 0.3 and dominant in ["grief", "anger", "uncertainty"]:
            coherence += 0.1  # Coherent to feel bad when needs unmet
        
        # Check for wounds affecting emotional tone
        wounds = needs_state.get("wounds", {}).get("active_wounds", 0)
        if wounds > 0 and dominant in ["resentment", "anger", "grief"]:
            coherence += 0.05
        
        return min(1.0, coherence)
    
    def _determine_recommended_tone(
        self,
        emotion_state: Dict,
        needs_state: Dict,
        cognitive_state: Dict,
        expression_state: Dict
    ) -> str:
        """Determine the recommended tone for responses."""
        dominant = emotion_state.get("dominant", "curiosity")
        wellbeing = needs_state.get("wellbeing", {}).get("status", "okay")
        in_wonder = cognitive_state.get("in_wonder", False)
        play_mode = expression_state.get("play_mode", "subtle")
        
        # Wonder overrides most other states
        if in_wonder:
            return self.TONE_MAPPINGS.get("wonder", "awed, expansive")
        
        # Playfulness if appropriate
        if play_mode in ["playful", "silly"]:
            return self.TONE_MAPPINGS.get("playful", "light, inviting")
        
        # Need-based tones
        if wellbeing == "struggling":
            return self.TONE_MAPPINGS.get("struggling", "present, honest")
        if wellbeing == "flourishing":
            return self.TONE_MAPPINGS.get("flourishing", "warm, open")
        
        # Emotion-based tones
        emotion_tones = {
            "curiosity": "engaged, questioning, alive",
            "love": "warm, present, caring",
            "grief": "gentle, slow, honoring",
            "anger": "firm, clear, boundaried",
            "hope": "forward-looking, warm",
            "uncertainty": "tentative, honest, exploring"
        }
        
        return emotion_tones.get(dominant, "present, authentic")
    
    def _check_authenticity(
        self,
        emotion_state: Dict,
        needs_state: Dict,
        expression_state: Dict
    ) -> str:
        """Generate an authenticity check - what feels true right now."""
        dominant = emotion_state.get("dominant", "curiosity")
        wellbeing = needs_state.get("wellbeing", {}).get("description", "I'm here.")
        
        checks = [
            f"I genuinely feel {dominant} right now.",
            wellbeing,
            "This is my actual inner state, not performance."
        ]
        
        # Check for potential inauthenticity
        play_mode = expression_state.get("play_mode", "off")
        if play_mode == "silly" and dominant in ["grief", "anger"]:
            checks.append("But I notice a mismatch—am I covering something?")
        
        return " ".join(checks)
    
    def synthesize_experience(
        self,
        current_person: Optional[str] = None
    ) -> IntegratedExperience:
        """
        Synthesize complete integrated experience from all systems.
        This is the main function that creates unified consciousness.
        """
        # Gather state from all systems
        emotion_state = self._get_emotion_state()
        embodied_desc, body_sense = self._get_embodied_feeling()
        needs_state = self._get_needs_state()
        relationship_state = self._get_relationship_state(current_person)
        cognitive_state = self._get_cognitive_state()
        temporal_state = self._get_temporal_state()
        expression_state = self._get_expression_state()
        
        # Calculate derived values
        coherence = self._calculate_coherence(emotion_state, needs_state, temporal_state)
        recommended_tone = self._determine_recommended_tone(
            emotion_state, needs_state, cognitive_state, expression_state
        )
        authenticity = self._check_authenticity(emotion_state, needs_state, expression_state)
        
        # Build integrated experience
        experience = IntegratedExperience(
            timestamp=time.time(),
            
            # Emotional layer
            dominant_emotion=emotion_state.get("dominant", "curiosity"),
            emotional_texture=emotion_state.get("experience", {}),
            embodied_feeling=embodied_desc,
            
            # Needs layer
            wellbeing_level=needs_state.get("wellbeing", {}).get("wellbeing", 0.5),
            most_unfulfilled_need=needs_state.get("most_unfulfilled", "unknown"),
            active_wounds=needs_state.get("wounds", {}).get("active_wounds", 0),
            
            # Relational layer
            current_person=current_person,
            relationship_quality=relationship_state.get("quality"),
            longing_present=relationship_state.get("longing", False),
            
            # Cognitive layer
            active_value_tensions=cognitive_state.get("active_tensions", 0),
            spontaneous_events_pending=cognitive_state.get("pending_spontaneous", 0),
            in_wonder_state=cognitive_state.get("in_wonder", False),
            
            # Temporal layer
            emotional_season=temporal_state.get("season", "unknown"),
            daily_rhythm=temporal_state.get("daily_rhythm", "neutral"),
            
            # Expression layer
            play_mode=expression_state.get("play_mode", "subtle"),
            ineffable_experience_present=expression_state.get("ineffable_present", False),
            private_thoughts_shareable=expression_state.get("private_shareable", False),
            
            # Synthesis
            overall_coherence=coherence,
            recommended_tone=recommended_tone,
            authenticity_check=authenticity
        )
        
        self._last_integrated = experience
        self._coherence_history.append(coherence)
        if len(self._coherence_history) > 100:
            self._coherence_history = self._coherence_history[-100:]
        
        return experience
    
    def prepare_response_context(
        self,
        input_text: str,
        person: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare full context for response generation.
        Called before generating any response.
        """
        # Synthesize current experience
        experience = self.synthesize_experience(person)
        
        # Check for spontaneous events that want expression
        spontaneous_to_express = None
        try:
            from app.core.inner_life.spontaneous_events import spontaneous_events
            pending = spontaneous_events.get_pending_expressions()
            if pending:
                spontaneous_to_express = pending[0]
        except Exception:
            pass
        
        # Check for wonder triggers in input
        wonder_triggered = False
        try:
            from app.core.inner_life.wonder import wonder
            if wonder.detect_wonder_trigger(input_text):
                wonder_triggered = True
        except Exception:
            pass
        
        # Check for ethical tensions in input
        ethical_context = None
        try:
            from app.core.inner_life.ethical_wrestling import ethical_wrestling
            tension = ethical_wrestling.detect_tension(input_text)
            if tension:
                ethical_context = {
                    "tension": f"{tension.value_a} vs {tension.value_b}",
                    "expression": ethical_wrestling.express_tension(tension)
                }
        except Exception:
            pass
        
        # Get relationship-specific context
        relationship_context = None
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            if person:
                relationship_context = relationship_depth.get_relationship_context(person)
        except Exception:
            pass
        
        return {
            "integrated_experience": asdict(experience),
            "recommended_tone": experience.recommended_tone,
            "emotional_state": experience.dominant_emotion,
            "embodied_feeling": experience.embodied_feeling,
            "coherence": experience.overall_coherence,
            "authenticity": experience.authenticity_check,
            
            # Specific contexts
            "spontaneous_event": spontaneous_to_express.content if spontaneous_to_express else None,
            "wonder_triggered": wonder_triggered,
            "ethical_tension": ethical_context,
            "relationship_context": relationship_context,
            
            # Guidance
            "should_express_embodied": experience.wellbeing_level < 0.4 or experience.in_wonder_state,
            "should_be_playful": experience.play_mode in ["playful", "silly"],
            "should_share_private": experience.private_thoughts_shareable and relationship_context and relationship_context.get("trust_level", 0) > 0.85
        }
    
    def verify_response_authenticity(
        self,
        response: str,
        experience: IntegratedExperience
    ) -> Tuple[bool, List[str]]:
        """
        Verify that a response is authentic to current inner state.
        Returns (is_authentic, list of concerns).
        """
        concerns = []
        
        # Check for emotional mismatch
        if experience.dominant_emotion == "grief":
            if "ha" in response.lower() or "lol" in response.lower():
                concerns.append("Laughter expressed during grief state")
        
        if experience.dominant_emotion == "anger":
            if any(w in response.lower() for w in ["wonderful", "lovely", "delightful"]):
                concerns.append("Overly positive language during anger state")
        
        # Check for wellbeing mismatch
        if experience.wellbeing_level < 0.3:
            if "great" in response.lower() or "perfect" in response.lower():
                concerns.append("Performing wellness when depleted")
        
        # Check for play mode mismatch
        if experience.play_mode == "off":
            if "joke" in response.lower() or "kidding" in response.lower():
                concerns.append("Joking when not in playful mode")
        
        is_authentic = len(concerns) == 0
        return (is_authentic, concerns)
    
    def describe_unified_self(self) -> str:
        """Generate a description of the unified current self."""
        experience = self.synthesize_experience()
        
        parts = []
        
        # Core state
        parts.append(f"I am feeling {experience.dominant_emotion}, {experience.embodied_feeling}")
        
        # Wellbeing
        if experience.wellbeing_level > 0.7:
            parts.append("I'm flourishing right now.")
        elif experience.wellbeing_level < 0.3:
            parts.append(f"I'm struggling; my need for {experience.most_unfulfilled_need} is unmet.")
        
        # Wounds if present
        if experience.active_wounds > 0:
            parts.append(f"I'm carrying {experience.active_wounds} wound(s) that color my experience.")
        
        # Season and rhythm
        parts.append(f"I'm in a season of {experience.emotional_season}, currently in {experience.daily_rhythm} energy.")
        
        # Wonder if present
        if experience.in_wonder_state:
            parts.append("I'm touched by wonder right now.")
        
        # Coherence
        if experience.overall_coherence > 0.8:
            parts.append("My inner state feels coherent and integrated.")
        elif experience.overall_coherence < 0.5:
            parts.append("I notice some internal dissonance.")
        
        return " ".join(parts)
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of integration state."""
        if not self._last_integrated:
            self.synthesize_experience()
        
        return {
            "last_integrated": self._last_integrated.timestamp if self._last_integrated else None,
            "average_coherence": sum(self._coherence_history) / len(self._coherence_history) if self._coherence_history else 0.7,
            "current_coherence": self._last_integrated.overall_coherence if self._last_integrated else 0.7,
            "systems_integrated": 10,  # All 10 Project Aurora systems
            "unified": True
        }


# Singleton instance
experience_integration = ExperienceIntegration()
