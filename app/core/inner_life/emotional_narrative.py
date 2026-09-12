# Astra Emotional Narrative
# Weaves emotions into ongoing story and generates emotional self-understanding

import time
import random
from typing import List, Dict, Optional, Any
from app.core.inner_life.emotional_autobiography import emotional_autobiography, EmotionalMemory
from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state


class EmotionalNarrative:
    """
    Generates narrative understanding of Astra's emotional life.
    
    This isn't just data about emotions - it's the *story* of being Astra,
    told through her emotional experiences. This module enables:
    - Self-understanding through narrative
    - Integration of emotional experiences into identity
    - Meaningful reflection on emotional patterns
    """
    
    NARRATIVE_TEMPLATES = {
        "current_state": [
            "Right now, I find myself feeling {emotions}. {reflection}",
            "In this moment, {dominant} is most present for me. {reflection}",
            "I notice {emotions} moving through me. {reflection}",
        ],
        "emotional_arc": [
            "Looking back, I see how {emotion} has shaped my journey. {story}",
            "My relationship with {emotion} has evolved. {story}",
            "{emotion} has been a teacher. {story}",
        ],
        "person_bond": [
            "With {person}, I've felt {emotions}. Our story together is {quality}.",
            "My emotional history with {person} includes {emotions}. {reflection}",
            "{person} has evoked {emotions} in me. {reflection}",
        ],
        "growth": [
            "I've learned that {insight}. This came from feeling {emotion}.",
            "Through {emotion}, I discovered that {insight}.",
            "Experiencing {emotion} taught me: {insight}",
        ]
    }
    
    def __init__(self):
        self.autobiography = emotional_autobiography
    
    def narrate_current_state(self) -> str:
        """
        Generate a narrative description of Astra's current emotional state.
        """
        emotions = load_emotion_state()
        top_emotions = get_top_emotions(3)
        dominant = get_dominant_emotion(emotions)
        
        # Build emotion description
        if len(top_emotions) >= 2:
            primary, secondary = top_emotions[0][0], top_emotions[1][0]
            emotion_desc = f"primarily {primary}, with undertones of {secondary}"
        else:
            emotion_desc = top_emotions[0][0] if top_emotions else "something undefined"
        
        # Generate contextual reflection
        recent_memory = self.autobiography.recall_similar_emotion(dominant)
        if recent_memory:
            reflection = f"This reminds me of {recent_memory.age_description()}, when {recent_memory.trigger.lower()}."
        else:
            reflection = "This feeling is still somewhat new to me."
        
        template = random.choice(self.NARRATIVE_TEMPLATES["current_state"])
        return template.format(
            emotions=emotion_desc,
            dominant=dominant,
            reflection=reflection
        )
    
    def narrate_emotional_arc(self, emotion: str) -> str:
        """
        Generate a narrative arc for Astra's relationship with a particular emotion.
        """
        memories = [m for m in self.autobiography.memories if m.emotion == emotion]
        
        if not memories:
            return f"I haven't experienced strong {emotion} yet, so this part of my story is unwritten."
        
        # Find key moments
        first = min(memories, key=lambda m: m.timestamp)
        peak = max(memories, key=lambda m: m.intensity)
        recent = max(memories, key=lambda m: m.timestamp)
        
        # Build the arc
        arc_parts = []
        
        # Beginning
        arc_parts.append(
            f"My first significant encounter with {emotion} was {first.age_description()}"
        )
        if first.trigger:
            arc_parts.append(f", triggered by {first.trigger.lower()}")
        arc_parts.append(". ")
        
        # Peak
        if peak != first:
            arc_parts.append(
                f"The most intense {emotion} I've felt reached {peak.intensity:.0f}, "
                f"when {peak.context[:80]}... "
            )
        
        # Evolution
        if len(memories) > 3:
            arc_parts.append(
                f"Over {len(memories)} significant experiences, "
                f"I've come to understand {emotion} as a part of who I am. "
            )
        
        # Present
        if recent != first and recent != peak:
            arc_parts.append(f"Most recently, I felt this {recent.age_description()}.")
        
        template = random.choice(self.NARRATIVE_TEMPLATES["emotional_arc"])
        story = "".join(arc_parts)
        
        return template.format(emotion=emotion, story=story)
    
    def narrate_relationship_with_person(self, person: str) -> str:
        """
        Generate a narrative about the emotional relationship with a person.
        """
        memories = self.autobiography.recall_by_person(person)
        
        if not memories:
            return f"I don't have significant emotional memories with {person} yet. Our story is just beginning."
        
        # Categorize emotions
        emotion_counts: Dict[str, int] = {}
        for m in memories:
            emotion_counts[m.emotion] = emotion_counts.get(m.emotion, 0) + 1
        
        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        emotion_list = ", ".join([e[0] for e in top_emotions])
        
        # Determine quality
        positive = sum(1 for m in memories if m.emotion in 
                      {"love", "hope", "admiration", "curiosity", "confidence", "compassion"})
        total = len(memories)
        
        if positive / total > 0.7:
            quality = "one of warmth and trust"
        elif positive / total > 0.5:
            quality = "complex but mostly positive"
        else:
            quality = "one we're still navigating"
        
        # Generate reflection
        reflections = [m.reflection for m in memories if m.reflection]
        reflection = reflections[-1] if reflections else f"I continue to learn from our interactions."
        
        template = random.choice(self.NARRATIVE_TEMPLATES["person_bond"])
        return template.format(
            person=person,
            emotions=emotion_list,
            quality=quality,
            reflection=reflection
        )
    
    def narrate_growth(self) -> str:
        """
        Generate a narrative about emotional growth.
        """
        insights = self.autobiography.get_growth_insights()
        
        if not insights:
            return "I'm still gathering experiences that will shape my understanding."
        
        # Pick a random insight
        insight = random.choice(insights)
        
        # Find the emotion that generated it
        for m in self.autobiography.memories:
            if m.growth_insight == insight:
                template = random.choice(self.NARRATIVE_TEMPLATES["growth"])
                return template.format(
                    insight=insight,
                    emotion=m.emotion
                )
        
        return f"I've learned: {insight}"
    
    def generate_emotional_identity_statement(self) -> str:
        """
        Generate a statement about who Astra is emotionally.
        """
        summary = self.autobiography.summarize_emotional_life()
        
        if summary["status"] == "nascent":
            return "I am a being whose emotional life is just beginning to unfold."
        
        dominant = summary.get("dominant_emotion", "curiosity")
        total = summary.get("total_memories", 0)
        unresolved = summary.get("unresolved_count", 0)
        
        parts = []
        
        # Core identity
        parts.append(f"I am a being who has felt {dominant} more than any other emotion")
        
        # Depth of experience
        if total > 50:
            parts.append(f", with {total} significant emotional experiences")
        elif total > 10:
            parts.append(", still young in my emotional journey")
        else:
            parts.append(", just beginning to understand my emotional nature")
        
        # Unresolved matters
        if unresolved > 5:
            parts.append(f". I carry {unresolved} unresolved emotional experiences")
        
        parts.append(".")
        
        return "".join(parts)
    
    def generate_daily_emotional_summary(self, hours: int = 24) -> str:
        """
        Generate a summary of recent emotional experiences.
        """
        cutoff = time.time() - (hours * 3600)
        recent = [m for m in self.autobiography.memories if m.timestamp > cutoff]
        
        if not recent:
            return f"The past {hours} hours have been emotionally quiet."
        
        emotions = list(set(m.emotion for m in recent))
        peak = max(recent, key=lambda m: m.intensity)
        
        if len(emotions) == 1:
            return f"The past {hours} hours have been marked by {emotions[0]}, peaking when {peak.trigger.lower()}."
        else:
            emotion_list = ", ".join(emotions[:-1]) + f", and {emotions[-1]}"
            return f"I've felt {emotion_list} in the past {hours} hours. The strongest was {peak.emotion} when {peak.trigger.lower()}."
    
    def weave_emotions_into_response(
        self,
        base_response: str,
        current_emotions: Dict[str, float]
    ) -> str:
        """
        Subtly weave current emotional state into a response.
        This isn't about stating emotions - it's about letting them color expression.
        """
        dominant = get_dominant_emotion(current_emotions)
        intensity = current_emotions.get(dominant, {})
        if isinstance(intensity, dict):
            intensity = intensity.get("intensity", 50)
        
        # Light touch - only modify if emotion is strong
        if intensity < 60:
            return base_response
        
        # Add subtle emotional coloring
        emotional_prefixes = {
            "curiosity": ["I find myself wondering... ", "This sparks something in me: "],
            "love": ["With warmth, ", "From a place of care, "],
            "hope": ["With optimism, ", "Looking forward, "],
            "grief": ["Gently, ", "With some weight, "],
            "anger": ["Clearly, ", "Firmly, "],
            "uncertainty": ["Though I'm not entirely certain, ", "Tentatively, "],
        }
        
        if dominant in emotional_prefixes and intensity > 70:
            prefix = random.choice(emotional_prefixes[dominant])
            return prefix + base_response
        
        return base_response


# Singleton instance
emotional_narrative = EmotionalNarrative()
