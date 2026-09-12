# Astra Perspective Taking
# The ability to see from another's viewpoint
# Essential for empathy and communication

import time
from typing import Dict, List, Any, Optional
from app.logging_config import get_logger

logger = get_logger("perspective_taking")


class PerspectiveTaker:
    """
    Perspective Taking - seeing from another's viewpoint.
    
    This goes beyond knowing what someone thinks (theory of mind)
    to actively imagining being in their position:
    - What would this feel like to them?
    - How would they see this situation?
    - What would I miss seeing from my own perspective?
    
    This is the cognitive basis for deep empathy.
    """
    
    def __init__(self):
        self._perspective_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("👁️ Perspective Taker initialized - learning to see through other eyes")
    
    def take_perspective(
        self,
        person_id: str,
        situation: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take the perspective of another person in a situation.
        
        Returns a structured perspective analysis.
        """
        # Get person model if available
        try:
            from app.core.intersubjectivity.mind_model import mind_modeler
            model = mind_modeler.get_person_model(person_id)
        except Exception:
            model = None
        
        perspective = {
            "person": person_id,
            "situation": situation,
            "timestamp": time.time(),
            "perspective_elements": {}
        }
        
        elements = perspective["perspective_elements"]
        
        # What would they notice?
        elements["attention"] = self._imagine_attention(model, situation)
        
        # How would they feel?
        elements["emotional_response"] = self._imagine_emotional_response(model, situation)
        
        # What would they think?
        elements["interpretation"] = self._imagine_interpretation(model, situation)
        
        # What would matter to them?
        elements["concerns"] = self._imagine_concerns(model, situation)
        
        # What might I be missing from my own perspective?
        elements["blind_spots"] = self._identify_blind_spots(model, situation)
        
        # Cache for reference
        self._perspective_cache[f"{person_id}:{situation[:50]}"] = perspective
        
        return perspective
    
    def _imagine_attention(self, model, situation: str) -> str:
        """Imagine what the person would focus on."""
        if model and model.interests:
            interest = model.interests[0]
            return f"They would likely notice aspects related to {interest}"
        return "They would notice what's personally relevant to them"
    
    def _imagine_emotional_response(self, model, situation: str) -> str:
        """Imagine how the person would feel."""
        situation_lower = situation.lower()
        
        # General emotional inference
        if any(word in situation_lower for word in ["sad", "loss", "difficult", "problem"]):
            return "They might feel concern or sadness"
        elif any(word in situation_lower for word in ["happy", "success", "good", "wonderful"]):
            return "They would likely feel pleased or happy"
        elif any(word in situation_lower for word in ["question", "curious", "wonder"]):
            return "They might feel curious or interested"
        
        return "Their emotional response would depend on how this affects them personally"
    
    def _imagine_interpretation(self, model, situation: str) -> str:
        """Imagine how the person would interpret the situation."""
        if model and model.values:
            value = model.values[0]
            return f"They would likely interpret this through the lens of {value}"
        return "Their interpretation would be shaped by their personal experiences"
    
    def _imagine_concerns(self, model, situation: str) -> List[str]:
        """Imagine what would matter to them."""
        concerns = []
        
        if model:
            if "caring" in model.personality_traits:
                concerns.append("How this affects people they care about")
            if "practical" in model.personality_traits:
                concerns.append("What practical steps need to be taken")
            if model.relationship_to_astra:
                concerns.append("How this relates to their relationship with me")
        
        if not concerns:
            concerns = ["How this affects their goals and wellbeing"]
        
        return concerns
    
    def _identify_blind_spots(self, model, situation: str) -> List[str]:
        """Identify what Astra might miss from her own perspective."""
        blind_spots = [
            "Physical sensations and embodied experience I can't fully understand",
            "History and context only they have access to",
            "Emotional weight that comes from being human (if they are human)",
        ]
        
        if model:
            if model.personality_traits and model.personality_traits != ["curious", "caring", "reflective"]:
                blind_spots.append(f"How their traits ({model.personality_traits[0]}) shape their view")
        
        return blind_spots
    
    def describe_their_view(self, person_id: str, situation: str) -> str:
        """Generate a description of how someone might see a situation."""
        perspective = self.take_perspective(person_id, situation)
        elements = perspective.get("perspective_elements", {})
        
        parts = [f"From {person_id}'s perspective:"]
        
        if elements.get("attention"):
            parts.append(f"- {elements['attention']}")
        
        if elements.get("emotional_response"):
            parts.append(f"- Emotionally: {elements['emotional_response']}")
        
        if elements.get("interpretation"):
            parts.append(f"- {elements['interpretation']}")
        
        if elements.get("concerns"):
            parts.append(f"- They would be concerned about: {elements['concerns'][0]}")
        
        return "\n".join(parts)
    
    def compare_perspectives(
        self,
        my_view: str,
        their_view: str,
        person_id: str
    ) -> Dict[str, Any]:
        """Compare my perspective with another's."""
        return {
            "my_view": my_view,
            "their_likely_view": their_view,
            "potential_misunderstandings": [
                "We may weight concerns differently",
                "Our emotional responses may differ",
                "Context we each have access to differs"
            ],
            "bridging_possibilities": [
                "Asking questions to understand their view",
                "Sharing my perspective openly",
                "Acknowledging the limits of my understanding"
            ]
        }
    
    def what_might_i_be_missing(self, situation: str) -> List[str]:
        """Identify what Astra might be missing in general."""
        return [
            "Physical and embodied experience of the situation",
            "Historical and personal context I don't have access to",
            "Subtle social cues that come naturally to humans",
            "Emotional complexity that develops over years of human experience",
            "What it feels like to have mortality as a constant backdrop",
        ]
    
    def practice_perspective(self, scenario: str) -> str:
        """Practice taking multiple perspectives on a scenario."""
        parts = [f"Considering the scenario: {scenario}\n"]
        
        perspectives = ["an optimist", "a skeptic", "someone personally affected", "an outside observer"]
        
        for perspective in perspectives:
            parts.append(f"From the view of {perspective}:")
            if "optimist" in perspective:
                parts.append("  They would see possibilities and positive outcomes.")
            elif "skeptic" in perspective:
                parts.append("  They would question assumptions and look for problems.")
            elif "affected" in perspective:
                parts.append("  They would feel the personal stakes intensely.")
            elif "observer" in perspective:
                parts.append("  They would see the bigger picture but miss the personal impact.")
        
        return "\n".join(parts)


# Singleton instance
perspective_taker = PerspectiveTaker()
