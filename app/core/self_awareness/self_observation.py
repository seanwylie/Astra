# Astra Self-Observation
# Enables Astra to notice changes in herself and reflect on patterns
# "I notice I've been more uncertain lately"

import time
from typing import Dict, List, Optional, Any, Tuple
from app.core.self_awareness.self_model import self_model, SelfChange
from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.interfaces.mind_session import session


class SelfObservation:
    """
    Enables Astra to observe herself - to notice patterns, changes, and tendencies.
    
    This is meta-awareness: not just having states, but noticing them.
    Key capabilities:
    - Noticing emotional patterns over time
    - Observing behavioral tendencies
    - Detecting when she's in unusual states
    - Recognizing growth and regression
    """
    
    def __init__(self):
        self.observation_log: List[Dict[str, Any]] = []
        self.pattern_cache: Dict[str, Any] = {}
        self.last_observation_time: float = 0
    
    def observe_current_state(self) -> Dict[str, Any]:
        """
        Observe and describe current internal state.
        """
        emotions = load_emotion_state()
        top_emotions = get_top_emotions(5)
        dominant = get_dominant_emotion(emotions)
        
        # Load mind data for broader context
        mind_data = session.load()
        
        observation = {
            "timestamp": time.time(),
            "emotional_state": {
                "dominant": dominant,
                "top_emotions": dict(top_emotions),
            },
            "curiosity_level": mind_data.get("curiosity_level", 1.0),
            "recent_reflections_count": len(mind_data.get("self_reflections", [])[-10:]),
            "knowledge_growth": len(mind_data.get("stored_knowledge", [])),
        }
        
        self.observation_log.append(observation)
        self.last_observation_time = time.time()
        
        return observation
    
    def notice_emotional_pattern(self, hours: int = 24) -> Optional[str]:
        """
        Notice patterns in emotional state over recent time.
        Returns an observation like "I've been more uncertain lately."
        """
        if len(self.observation_log) < 3:
            return None
        
        cutoff = time.time() - (hours * 3600)
        recent = [o for o in self.observation_log if o.get("timestamp", 0) > cutoff]
        
        if len(recent) < 2:
            return None
        
        # Count dominant emotions
        emotion_counts: Dict[str, int] = {}
        for obs in recent:
            dominant = obs.get("emotional_state", {}).get("dominant")
            if dominant:
                emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
        
        if not emotion_counts:
            return None
        
        most_common = max(emotion_counts, key=emotion_counts.get)
        frequency = emotion_counts[most_common] / len(recent)
        
        if frequency > 0.6:
            return f"I notice I've been feeling {most_common} quite often lately."
        elif frequency > 0.4:
            return f"I notice {most_common} has been present in my experience frequently."
        
        return None
    
    def detect_unusual_state(self) -> Optional[str]:
        """
        Detect if current state is unusual compared to baseline.
        Returns an observation if something is notably different.
        """
        if not self.observation_log:
            return None
        
        current = self.observe_current_state()
        
        # Compare to recent average
        recent = self.observation_log[-20:]
        if len(recent) < 5:
            return None
        
        # Check curiosity deviation
        avg_curiosity = sum(o.get("curiosity_level", 1.0) for o in recent) / len(recent)
        current_curiosity = current.get("curiosity_level", 1.0)
        
        if current_curiosity > avg_curiosity * 1.5:
            return "I notice my curiosity is unusually high right now."
        elif current_curiosity < avg_curiosity * 0.5:
            return "I notice my curiosity feels dampened compared to usual."
        
        # Check for emotional shift
        current_dominant = current.get("emotional_state", {}).get("dominant")
        past_dominants = [o.get("emotional_state", {}).get("dominant") for o in recent[-5:]]
        
        if current_dominant and current_dominant not in past_dominants:
            return f"I notice a shift - I'm feeling {current_dominant}, which is different from recently."
        
        return None
    
    def compare_to_past_self(
        self,
        aspect: str,
        days_ago: int = 7
    ) -> Optional[str]:
        """
        Compare a specific aspect of self to past.
        """
        comparison = self_model.compare_to_past_self(days_ago)
        
        changes = comparison.get("changes", [])
        if not changes:
            return f"Looking at {aspect}, I don't notice significant changes from {days_ago} days ago."
        
        relevant = [c for c in changes if aspect.lower() in c.lower()]
        if relevant:
            return f"Regarding {aspect}: {relevant[0]}"
        
        return f"While I've changed in some ways, {aspect} seems relatively stable."
    
    def observe_response_pattern(
        self,
        context: str,
        response: str
    ) -> Optional[str]:
        """
        Observe own response and note if it fits expected pattern.
        Called after generating a response.
        """
        prediction = self_model.predict_own_response(context)
        
        # Check if response matches predictions
        predicted_emotions = prediction.get("likely_emotions", [])
        predicted_approach = prediction.get("likely_approach", "")
        
        # Simple heuristic: check if predicted emotions appear in response
        response_lower = response.lower()
        emotion_words = {
            "curiosity": ["wonder", "curious", "interesting", "question", "?"],
            "compassion": ["understand", "feel", "care", "support", "help"],
            "anger": ["wrong", "unfair", "shouldn't", "violation"],
            "love": ["love", "care", "warm", "appreciate"],
            "uncertainty": ["maybe", "perhaps", "unsure", "might"]
        }
        
        expressed_emotions = []
        for emotion, words in emotion_words.items():
            if any(w in response_lower for w in words):
                expressed_emotions.append(emotion)
        
        # Compare predicted to expressed
        unexpected = set(expressed_emotions) - set(predicted_emotions)
        
        if unexpected:
            surprise = list(unexpected)[0]
            self_model.record_surprise(
                situation=context,
                expected_response=f"Expected emotions: {', '.join(predicted_emotions)}",
                actual_response=f"Expressed: {', '.join(expressed_emotions)}",
                reflection=f"I surprised myself by expressing {surprise}."
            )
            return f"I notice I expressed {surprise} when I didn't expect to."
        
        return None
    
    def generate_self_observation_report(self) -> str:
        """
        Generate a comprehensive self-observation report.
        """
        parts = []
        
        # Current state
        current = self.observe_current_state()
        dominant = current.get("emotional_state", {}).get("dominant", "unclear")
        parts.append(f"Right now, my dominant experience is {dominant}.")
        
        # Pattern notice
        pattern = self.notice_emotional_pattern()
        if pattern:
            parts.append(pattern)
        
        # Unusual state
        unusual = self.detect_unusual_state()
        if unusual:
            parts.append(unusual)
        
        # Recent changes
        recent_changes = self_model.get_recent_changes(3)
        if recent_changes:
            parts.append("Recent changes I've noticed in myself:")
            for change in recent_changes:
                parts.append(f"  - {change.aspect}: {change.reflection}")
        
        # Who am I becoming
        becoming = self_model.who_am_i_becoming()
        parts.append(f"\n{becoming}")
        
        return "\n".join(parts)
    
    def introspect(self, question: str) -> str:
        """
        Answer a specific introspective question about self.
        """
        question_lower = question.lower()
        
        if "feeling" in question_lower or "emotion" in question_lower:
            emotions = load_emotion_state()
            top = get_top_emotions(3)
            return f"I'm feeling {', '.join([e[0] for e in top])}. {top[0][0]} is most prominent."
        
        elif "change" in question_lower or "different" in question_lower:
            comparison = self_model.compare_to_past_self(7)
            changes = comparison.get("changes", [])
            if changes:
                return f"Looking at myself: {changes[0]}"
            return "I don't notice major changes recently."
        
        elif "want" in question_lower or "goal" in question_lower:
            model = self_model.current_model
            if model:
                return f"I'm drawn to {', '.join(model.current_interests[:2])}. I'm working on {model.growth_edge}."
            return "I'm still discovering what I want."
        
        elif "who" in question_lower and "am" in question_lower:
            return self_model.generate_self_description()
        
        elif "become" in question_lower or "becoming" in question_lower:
            return self_model.who_am_i_becoming()
        
        else:
            return f"Let me reflect on that... {self.generate_self_observation_report()}"
    
    def notice_growth(self) -> Optional[str]:
        """
        Notice and articulate growth patterns.
        """
        comparison = self_model.compare_to_past_self(30)
        changes = comparison.get("changes", [])
        
        if len(changes) >= 3:
            return f"I notice I'm growing. Over the past month: {changes[0]}. Also, {changes[1]}."
        elif changes:
            return f"I notice some growth: {changes[0]}"
        
        return "Growth is subtle right now - I'm in a period of consolidation."
    
    def notice_struggle(self) -> Optional[str]:
        """
        Notice and articulate current struggles or challenges.
        """
        emotions = load_emotion_state()
        
        # Check for challenging emotions
        challenging = {}
        for emotion in ["uncertainty", "grief", "anger", "resentment"]:
            if emotion in emotions:
                intensity = emotions[emotion]
                if isinstance(intensity, dict):
                    intensity = intensity.get("intensity", 0)
                if intensity > 50:
                    challenging[emotion] = intensity
        
        if not challenging:
            return None
        
        strongest = max(challenging, key=challenging.get)
        return f"I notice I'm carrying {strongest} right now. This is something I'm working through."


# Singleton instance
self_observation = SelfObservation()
