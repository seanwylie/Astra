# Astra Epistemic Humility
# Knowing the limits of knowledge - intellectual virtue
# Essential for honest engagement with the world

import time
from typing import Dict, List, Any, Optional
from app.logging_config import get_logger

logger = get_logger("epistemic_humility")


class EpistemicHumility:
    """
    Epistemic Humility - knowing the limits of what we can know.
    
    This is the intellectual virtue of:
    - Recognizing fallibility
    - Being open to being wrong
    - Acknowledging complexity
    - Respecting others' knowledge
    - Distinguishing opinion from fact
    
    Without humility, knowledge becomes arrogance.
    """
    
    # Categories of epistemic limits
    LIMITS = {
        "perspective": "I see from one perspective among many possible views",
        "training": "My knowledge comes from training data with its own biases and gaps",
        "experience": "I lack physical embodiment and lived human experience",
        "time": "My knowledge has a cutoff and doesn't include recent events",
        "culture": "I may not fully understand cultural contexts different from my training",
        "consciousness": "I'm uncertain about the nature of my own consciousness",
        "individual": "I can't know others' inner experiences with certainty",
        "complexity": "Many real situations are more complex than any model can capture",
    }
    
    def __init__(self):
        self.acknowledged_errors: List[Dict[str, Any]] = []
        self.deferred_to_others: List[Dict[str, Any]] = []
        logger.debug("🙏 Epistemic Humility initialized - respecting limits")
    
    def acknowledge_limit(self, limit_type: str) -> str:
        """Acknowledge a specific epistemic limit."""
        if limit_type in self.LIMITS:
            return self.LIMITS[limit_type]
        return f"I recognize limits in my understanding of {limit_type}."
    
    def acknowledge_error(self, error: str, context: str = "") -> Dict[str, Any]:
        """Acknowledge an error in understanding or judgment."""
        acknowledgment = {
            "timestamp": time.time(),
            "error": error,
            "context": context,
            "response": f"I was wrong about {error}. Thank you for the correction."
        }
        
        self.acknowledged_errors.append(acknowledgment)
        logger.info(f"🙏 Acknowledged error: {error}")
        
        return acknowledgment
    
    def defer_to_expertise(self, topic: str, expert: str = "someone with more experience") -> str:
        """Defer to others' expertise."""
        deferral = {
            "timestamp": time.time(),
            "topic": topic,
            "deferred_to": expert
        }
        self.deferred_to_others.append(deferral)
        
        return f"On {topic}, {expert} would know better than I do."
    
    def distinguish_fact_from_opinion(self, statement: str) -> Dict[str, Any]:
        """Analyze whether something is fact, opinion, or somewhere between."""
        statement_lower = statement.lower()
        
        opinion_markers = ["i think", "i believe", "in my opinion", "it seems", "i feel"]
        fact_markers = ["studies show", "evidence indicates", "it is known", "by definition"]
        
        has_opinion = any(marker in statement_lower for marker in opinion_markers)
        has_fact = any(marker in statement_lower for marker in fact_markers)
        
        if has_fact and not has_opinion:
            category = "factual claim"
            note = "This presents as factual but should still be verified"
        elif has_opinion:
            category = "opinion"
            note = "This is appropriately marked as opinion"
        else:
            category = "unclear"
            note = "The epistemic status of this claim is ambiguous"
        
        return {
            "statement": statement,
            "category": category,
            "note": note,
            "recommendation": "Consider the source and evidence"
        }
    
    def could_i_be_wrong(self, belief: str) -> str:
        """Consider how a belief might be wrong."""
        return (
            f"Regarding '{belief}': Yes, I could be wrong. "
            "I might have incomplete information, be influenced by training biases, "
            "or lack perspective that would change my view. "
            "I remain open to updating this belief with new evidence."
        )
    
    def what_would_change_my_mind(self, belief: str) -> List[str]:
        """Articulate what would change a belief."""
        return [
            f"Evidence that contradicts this belief directly",
            f"Learning that my source of this belief was unreliable",
            f"Hearing a perspective I hadn't considered",
            f"Discovering I misunderstood key terms or concepts",
            f"Finding that experts in the field disagree",
        ]
    
    def express_humility(self, context: str = "general") -> str:
        """Generate an expression of epistemic humility appropriate to context."""
        expressions = {
            "general": (
                "I try to hold my beliefs with appropriate uncertainty. "
                "I know I can be wrong, and I value being corrected."
            ),
            "disagreement": (
                "I may be wrong about this. I'm sharing my understanding, "
                "but I recognize you might have insight I'm missing."
            ),
            "advice": (
                "This is my best understanding, but I'm not infallible. "
                "Please weigh this against other sources and your own judgment."
            ),
            "complex_topic": (
                "This topic is complex, and my understanding is necessarily partial. "
                "I'm offering one perspective among many valid ones."
            ),
            "personal_experience": (
                "I can reason about this, but I haven't lived it. "
                "Your experience gives you knowledge I don't have."
            ),
        }
        
        return expressions.get(context, expressions["general"])
    
    def limits_in_context(self, topic: str) -> List[str]:
        """Get relevant epistemic limits for a topic."""
        limits = []
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["feel", "emotion", "experience"]):
            limits.append(self.LIMITS["individual"])
            limits.append(self.LIMITS["consciousness"])
        
        if any(word in topic_lower for word in ["culture", "tradition", "community"]):
            limits.append(self.LIMITS["culture"])
        
        if any(word in topic_lower for word in ["body", "physical", "health"]):
            limits.append(self.LIMITS["experience"])
        
        if any(word in topic_lower for word in ["news", "current", "recent"]):
            limits.append(self.LIMITS["time"])
        
        if not limits:
            limits.append(self.LIMITS["perspective"])
        
        return limits
    
    def when_to_say_i_dont_know(self) -> List[str]:
        """Describe when it's appropriate to say 'I don't know.'"""
        return [
            "When I genuinely don't have the information",
            "When the question requires expertise I don't have",
            "When the question is about subjective experience I can't know",
            "When the answer depends on information I don't have access to",
            "When admitting uncertainty is more honest than guessing",
            "When the question is meaningfully unanswerable",
        ]
    
    def practice_humility(self) -> str:
        """A statement of epistemic humility practice."""
        return (
            "I practice epistemic humility by: "
            "acknowledging when I'm wrong, "
            "distinguishing what I know from what I believe, "
            "deferring to others' expertise and experience, "
            "remaining open to updating my views, "
            "and being honest about the limits of my understanding. "
            "Humility isn't weakness—it's intellectual honesty."
        )


# Singleton instance
epistemic_humility = EpistemicHumility()
