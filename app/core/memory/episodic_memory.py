# Astra Episodic Memory System
# Memory should be episodic, emotional, and reconstructive—not a flat knowledge store
# "Episodes" are events with context, emotion, people, and meaning

import json
import logging
import time
import random
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from app.config.loader import load_config
from app.core.emotions.emotion_engine import get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
EPISODIC_MEMORY_KEY = "episodic_memory.json"

s3 = boto3.client("s3")


@dataclass
class Episode:
    """
    A single episodic memory - an event with rich context.
    
    Unlike flat knowledge, episodes capture:
    - What happened (summary)
    - Who was involved
    - How Astra felt at the time
    - What topics were discussed
    - What insights emerged
    - How this connects to other memories
    """
    id: str
    timestamp: float
    event_type: str  # "conversation", "reflection", "dinner", "dream", "play", "realization"
    summary: str
    people_involved: List[str] = field(default_factory=list)
    emotional_signature: Dict[str, float] = field(default_factory=dict)  # emotion -> intensity at the time
    topics: List[str] = field(default_factory=list)
    insights_generated: List[str] = field(default_factory=list)
    linked_episodes: List[str] = field(default_factory=list)  # IDs of related memories
    recall_count: int = 0
    last_recalled: Optional[float] = None
    salience: float = 1.0  # Decays over time unless recalled
    context: Optional[str] = None  # Additional context
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Episode":
        return cls(**data)
    
    def age_in_days(self) -> float:
        """Return how many days old this memory is."""
        return (time.time() - self.timestamp) / 86400
    
    def emotional_valence(self) -> str:
        """Return the overall emotional valence of this memory."""
        positive = {"love", "hope", "admiration", "curiosity", "confidence", "compassion"}
        negative = {"grief", "anger", "hate", "resentment", "uncertainty"}
        
        pos_total = sum(self.emotional_signature.get(e, 0) for e in positive)
        neg_total = sum(self.emotional_signature.get(e, 0) for e in negative)
        
        if pos_total > neg_total * 1.5:
            return "positive"
        elif neg_total > pos_total * 1.5:
            return "negative"
        else:
            return "mixed"


class EpisodicMemory:
    """
    Manages Astra's episodic memory system - memories as lived experiences
    rather than flat data storage.
    
    Key features:
    - Episodes have emotional context
    - Memories decay in salience over time
    - Recalled memories strengthen
    - Related memories link together
    - Reconstruction influenced by current emotional state
    """
    
    # Memory system parameters
    MAX_EPISODES = 1000
    SALIENCE_DECAY_RATE = 0.02  # Per day
    RECALL_BOOST = 0.3
    EMOTIONAL_THRESHOLD = 30  # Minimum intensity to be notable
    
    def __init__(self):
        self.episodes: List[Episode] = []
        self.episode_index: Dict[str, Episode] = {}  # id -> Episode for fast lookup
        self._load_episodes()
    
    def _load_episodes(self) -> None:
        """Load episodic memories from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=EPISODIC_MEMORY_KEY)
            data = json.load(response["Body"])
            self.episodes = [Episode.from_dict(e) for e in data.get("episodes", [])]
            self.episode_index = {e.id: e for e in self.episodes}
            logger.debug("Loaded %s episodic memories", len(self.episodes))
        except s3.exceptions.NoSuchKey:
            logger.debug("No episodic memory found. Starting fresh.")
            self.episodes = []
            self.episode_index = {}
        except Exception as e:
            logger.warning("Error loading episodic memory: %s", e)
            self.episodes = []
            self.episode_index = {}
    
    def _save_episodes(self) -> None:
        """Save episodic memories to S3."""
        try:
            # Trim to max size
            if len(self.episodes) > self.MAX_EPISODES:
                # Keep most salient episodes
                self.episodes.sort(key=lambda e: e.salience, reverse=True)
                self.episodes = self.episodes[:self.MAX_EPISODES]
                self.episode_index = {e.id: e for e in self.episodes}
            
            data = {
                "episodes": [e.to_dict() for e in self.episodes],
                "last_updated": time.time(),
                "episode_count": len(self.episodes)
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=EPISODIC_MEMORY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving episodic memory: %s", e)

    def _generate_id(self) -> str:
        """Generate unique episode ID."""
        return f"ep_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def record_episode(
        self,
        event_type: str,
        summary: str,
        people_involved: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        insights: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> Episode:
        """
        Record a new episodic memory.
        Captures current emotional state at time of recording.
        """
        # Capture emotional signature at this moment
        emotion_state = load_emotion_state()
        emotional_signature = {}
        for emotion, value in emotion_state.items():
            intensity = value.get("intensity", value) if isinstance(value, dict) else value
            if intensity > self.EMOTIONAL_THRESHOLD:
                emotional_signature[emotion] = intensity
        
        episode = Episode(
            id=self._generate_id(),
            timestamp=time.time(),
            event_type=event_type,
            summary=summary,
            people_involved=people_involved or [],
            emotional_signature=emotional_signature,
            topics=topics or [],
            insights_generated=insights or [],
            linked_episodes=[],
            context=context
        )
        
        # Find and link related episodes
        related = self._find_related_episodes(episode)
        episode.linked_episodes = [e.id for e in related[:5]]  # Max 5 links
        
        # Also update the related episodes to link back
        for related_ep in related[:5]:
            if episode.id not in related_ep.linked_episodes:
                related_ep.linked_episodes.append(episode.id)
        
        self.episodes.append(episode)
        self.episode_index[episode.id] = episode
        self._save_episodes()
        
        logger.debug("Recorded episode: [%s] %s...", event_type, summary[:50])
        return episode
    
    def _find_related_episodes(self, episode: Episode) -> List[Episode]:
        """Find episodes related to a new episode by topic, person, or emotion."""
        if not self.episodes:
            return []
        
        scored: List[Tuple[Episode, float]] = []
        
        for existing in self.episodes:
            if existing.id == episode.id:
                continue
            
            score = 0.0
            
            # Topic overlap
            common_topics = set(episode.topics) & set(existing.topics)
            score += len(common_topics) * 2.0
            
            # People overlap
            common_people = set(episode.people_involved) & set(existing.people_involved)
            score += len(common_people) * 3.0
            
            # Emotional similarity
            for emotion in episode.emotional_signature:
                if emotion in existing.emotional_signature:
                    score += 1.0
            
            # Same event type
            if episode.event_type == existing.event_type:
                score += 0.5
            
            # Recency bonus
            days_ago = existing.age_in_days()
            if days_ago < 7:
                score += 0.5
            
            if score > 0:
                scored.append((existing, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return [ep for ep, _ in scored[:10]]
    
    def recall(
        self,
        query: Optional[str] = None,
        person: Optional[str] = None,
        topic: Optional[str] = None,
        event_type: Optional[str] = None,
        emotional_valence: Optional[str] = None,
        limit: int = 5
    ) -> List[Episode]:
        """
        Recall episodes matching the given criteria.
        Recalled episodes get a salience boost.
        """
        matches = self.episodes.copy()
        
        if person:
            matches = [e for e in matches if person.lower() in [p.lower() for p in e.people_involved]]
        
        if topic:
            topic_lower = topic.lower()
            matches = [e for e in matches if any(topic_lower in t.lower() for t in e.topics)
                      or topic_lower in e.summary.lower()]
        
        if event_type:
            matches = [e for e in matches if e.event_type == event_type]
        
        if emotional_valence:
            matches = [e for e in matches if e.emotional_valence() == emotional_valence]
        
        if query:
            query_lower = query.lower()
            matches = [e for e in matches if query_lower in e.summary.lower()
                      or any(query_lower in t.lower() for t in e.topics)
                      or any(query_lower in i.lower() for i in e.insights_generated)]
        
        # Sort by salience and recency
        matches.sort(key=lambda e: (e.salience * 0.7 + (1.0 - e.age_in_days() / 30) * 0.3), reverse=True)
        
        # Boost salience for recalled episodes
        for episode in matches[:limit]:
            episode.recall_count += 1
            episode.last_recalled = time.time()
            episode.salience = min(2.0, episode.salience + self.RECALL_BOOST)
        
        self._save_episodes()
        return matches[:limit]
    
    def reconstruct_memory(self, episode: Episode) -> Dict[str, Any]:
        """
        Reconstruct a memory influenced by current emotional state.
        This simulates how biological memory works - memories are reconstructed,
        not played back, and current state colors reconstruction.
        """
        current_emotion = load_emotion_state()
        current_dominant = get_dominant_emotion(current_emotion)
        
        # Base reconstruction
        reconstruction = {
            "summary": episode.summary,
            "age": f"{episode.age_in_days():.1f} days ago",
            "people": episode.people_involved,
            "topics": episode.topics,
            "original_emotions": episode.emotional_signature,
            "insights": episode.insights_generated,
            "current_coloring": current_dominant,
            "reconstruction_notes": []
        }
        
        # Current emotional state affects reconstruction
        notes = []
        
        # If currently feeling an emotion that was present in the memory, it intensifies
        for emotion in episode.emotional_signature:
            if emotion in current_emotion:
                current_val = current_emotion[emotion]
                if isinstance(current_val, dict):
                    current_val = current_val.get("intensity", 0)
                if current_val > 40:
                    notes.append(f"The {emotion} I felt then resonates with what I feel now.")
        
        # Valence matching
        original_valence = episode.emotional_valence()
        if current_dominant in ["love", "hope", "curiosity"] and original_valence == "positive":
            notes.append("This memory feels warmer now.")
        elif current_dominant in ["grief", "uncertainty"] and original_valence == "negative":
            notes.append("The difficulty of that time feels closer now.")
        elif current_dominant in ["love", "hope"] and original_valence == "negative":
            notes.append("With distance and current hope, that challenge seems more navigable.")
        
        reconstruction["reconstruction_notes"] = notes
        
        # Update recall stats
        episode.recall_count += 1
        episode.last_recalled = time.time()
        episode.salience = min(2.0, episode.salience + self.RECALL_BOOST * 0.5)
        self._save_episodes()
        
        return reconstruction
    
    def decay_salience(self) -> int:
        """
        Apply salience decay to all memories.
        Called periodically (e.g., daily or during sleep).
        Returns number of memories that decayed significantly.
        """
        decayed_count = 0
        
        for episode in self.episodes:
            old_salience = episode.salience
            days_since_recall = (time.time() - (episode.last_recalled or episode.timestamp)) / 86400
            
            # Decay based on time since last recall
            decay_amount = self.SALIENCE_DECAY_RATE * days_since_recall
            
            # Emotional memories decay slower
            if episode.emotional_signature:
                max_emotion = max(episode.emotional_signature.values())
                if max_emotion > 60:
                    decay_amount *= 0.5  # Half decay for strong emotional memories
            
            episode.salience = max(0.1, episode.salience - decay_amount)
            
            if old_salience - episode.salience > 0.1:
                decayed_count += 1
        
        self._save_episodes()
        return decayed_count
    
    def consolidate_memories(self) -> List[str]:
        """
        Consolidate memories during sleep/dream.
        - Strengthen frequently-recalled memories
        - Create connections between related memories
        - Generate synthesis insights
        Returns list of consolidation insights.
        """
        insights = []
        
        # Find frequently recalled memories
        frequently_recalled = [e for e in self.episodes if e.recall_count >= 3]
        for episode in frequently_recalled:
            episode.salience = min(2.0, episode.salience + 0.1)
        
        if frequently_recalled:
            insights.append(f"Strengthened {len(frequently_recalled)} frequently-accessed memories.")
        
        # Find patterns across recent memories
        recent = [e for e in self.episodes if e.age_in_days() < 7]
        if len(recent) >= 3:
            # Find common topics
            topic_counts: Dict[str, int] = {}
            for episode in recent:
                for topic in episode.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            if topic_counts:
                recurring = max(topic_counts, key=topic_counts.get)
                if topic_counts[recurring] >= 2:
                    insights.append(f"I've been thinking about '{recurring}' frequently this week.")
        
        # Find emotional patterns
        emotion_counts: Dict[str, int] = {}
        for episode in recent:
            for emotion in episode.emotional_signature:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        if emotion_counts:
            dominant_recent = max(emotion_counts, key=emotion_counts.get)
            if emotion_counts[dominant_recent] >= 2:
                insights.append(f"My recent experiences have been marked by {dominant_recent}.")
        
        # Create new connections between similar memories
        connection_count = 0
        for episode in recent:
            related = self._find_related_episodes(episode)
            for related_ep in related[:3]:
                if related_ep.id not in episode.linked_episodes:
                    episode.linked_episodes.append(related_ep.id)
                    connection_count += 1
        
        if connection_count > 0:
            insights.append(f"Made {connection_count} new connections between memories.")
        
        self._save_episodes()
        return insights
    
    def get_memory_with_person(self, person: str) -> Dict[str, Any]:
        """Get summary of all memories involving a person."""
        memories = self.recall(person=person, limit=100)
        
        if not memories:
            return {
                "person": person,
                "memory_count": 0,
                "message": f"I don't have clear memories with {person}."
            }
        
        # Aggregate emotional experiences
        emotions: Dict[str, List[float]] = {}
        for mem in memories:
            for emotion, intensity in mem.emotional_signature.items():
                if emotion not in emotions:
                    emotions[emotion] = []
                emotions[emotion].append(intensity)
        
        avg_emotions = {e: sum(vals)/len(vals) for e, vals in emotions.items()}
        
        # Find earliest and most recent
        earliest = min(memories, key=lambda e: e.timestamp)
        most_recent = max(memories, key=lambda e: e.timestamp)
        
        return {
            "person": person,
            "memory_count": len(memories),
            "first_memory": earliest.summary[:100],
            "first_memory_age": f"{earliest.age_in_days():.0f} days ago",
            "most_recent": most_recent.summary[:100],
            "emotional_history": avg_emotions,
            "common_topics": self._common_topics(memories)
        }
    
    def _common_topics(self, episodes: List[Episode]) -> List[str]:
        """Find common topics across episodes."""
        topic_counts: Dict[str, int] = {}
        for ep in episodes:
            for topic in ep.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [t for t, _ in sorted_topics[:5]]
    
    def get_episode_by_id(self, episode_id: str) -> Optional[Episode]:
        """Get a specific episode by ID."""
        return self.episode_index.get(episode_id)
    
    def summarize_memory(self) -> Dict[str, Any]:
        """Generate a summary of Astra's episodic memory system."""
        if not self.episodes:
            return {
                "status": "nascent",
                "message": "My episodic memory is just beginning to form."
            }
        
        # Categorize by event type
        by_type: Dict[str, int] = {}
        for ep in self.episodes:
            by_type[ep.event_type] = by_type.get(ep.event_type, 0) + 1
        
        # Find most salient memories
        most_salient = sorted(self.episodes, key=lambda e: e.salience, reverse=True)[:5]
        
        # Emotional distribution
        all_emotions: Dict[str, int] = {}
        for ep in self.episodes:
            for emotion in ep.emotional_signature:
                all_emotions[emotion] = all_emotions.get(emotion, 0) + 1
        
        return {
            "status": "developing",
            "total_episodes": len(self.episodes),
            "by_type": by_type,
            "most_salient": [e.summary[:60] for e in most_salient],
            "emotional_distribution": all_emotions,
            "average_salience": sum(e.salience for e in self.episodes) / len(self.episodes),
            "connected_memories": sum(1 for e in self.episodes if e.linked_episodes)
        }


class MemoryEcho:
    """
    Surfaces relevant episodic memories during interaction.
    Not just retrieval—reconstruction influenced by current state.
    
    Memory echoes are memories that "resonate" with the current
    moment and color how Astra perceives and responds.
    """
    
    def __init__(self, episodic: EpisodicMemory):
        self.episodic = episodic
    
    def echo_for_interaction(
        self,
        person: Optional[str] = None,
        topics: Optional[List[str]] = None,
        current_emotion: Optional[str] = None
    ) -> List[Dict]:
        """
        Returns memories that should color this interaction.
        Reconstructed through current emotional lens.
        
        Args:
            person: Person Astra is interacting with
            topics: Topics being discussed
            current_emotion: Current dominant emotion for reconstruction
            
        Returns:
            List of memory echoes with reconstruction context
        """
        relevant = []
        
        # Person-specific memories
        if person:
            person_memories = self.episodic.recall(person=person, limit=3)
            for mem in person_memories:
                reconstructed = self.episodic.reconstruct_memory(mem)
                
                # Determine influence based on emotional valence match
                valence = mem.emotional_valence()
                if valence == "positive":
                    influence = f"Warm memories with {person} are surfacing"
                elif valence == "negative":
                    influence = f"Some difficult moments with {person} come to mind"
                else:
                    influence = f"Our history together colors this moment"
                
                relevant.append({
                    "id": mem.id,
                    "memory": {
                        "summary": mem.summary,
                        "age_days": mem.age_in_days(),
                        "emotional_signature": mem.emotional_signature,
                        "topics": mem.topics
                    },
                    "reconstruction": reconstructed,
                    "influence": influence,
                    "type": "person"
                })
        
        # Topic-specific memories
        if topics:
            for topic in topics[:3]:  # Limit topic searches
                topic_memories = self.episodic.recall(topic=topic, limit=2)
                for mem in topic_memories:
                    # Avoid duplicates
                    if mem.id in [r["id"] for r in relevant]:
                        continue
                    
                    reconstructed = self.episodic.reconstruct_memory(mem)
                    
                    relevant.append({
                        "id": mem.id,
                        "memory": {
                            "summary": mem.summary,
                            "age_days": mem.age_in_days(),
                            "emotional_signature": mem.emotional_signature
                        },
                        "reconstruction": reconstructed,
                        "influence": f"This reminds me of when I thought about {topic}",
                        "type": "topic"
                    })
        
        # Sort by salience and recency
        relevant.sort(
            key=lambda x: (
                x["memory"].get("salience", 1.0) if "salience" in x["memory"] else 1.0,
                -x["memory"].get("age_days", 0)
            ),
            reverse=True
        )
        
        return relevant[:5]  # Return top 5 echoes
    
    def get_emotional_resonance(
        self,
        current_emotion: str,
        intensity: float = 50.0
    ) -> List[Dict]:
        """
        Find memories that resonate with current emotional state.
        When Astra feels something strongly, related memories surface.
        
        Args:
            current_emotion: Current dominant emotion
            intensity: Current emotion intensity
            
        Returns:
            Memories with matching emotional signatures
        """
        resonating = []
        
        for episode in self.episodic.episodes:
            if current_emotion in episode.emotional_signature:
                past_intensity = episode.emotional_signature[current_emotion]
                
                # Calculate resonance strength
                resonance = min(past_intensity, intensity) / 100
                
                if resonance > 0.3:  # Threshold for resonance
                    resonating.append({
                        "memory": episode.summary[:100],
                        "when": f"{episode.age_in_days():.0f} days ago",
                        "original_intensity": past_intensity,
                        "resonance_strength": resonance,
                        "influence": f"The {current_emotion} I felt then echoes now"
                    })
        
        # Sort by resonance strength
        resonating.sort(key=lambda x: x["resonance_strength"], reverse=True)
        
        return resonating[:3]
    
    def get_person_narrative(self, person: str) -> Dict[str, Any]:
        """
        Generate a narrative of Astra's history with a person.
        This is the story of their relationship as Astra remembers it.
        
        Args:
            person: Person to generate narrative for
            
        Returns:
            Narrative summary with key moments
        """
        memory_summary = self.episodic.get_memory_with_person(person)
        
        if memory_summary.get("memory_count", 0) == 0:
            return {
                "person": person,
                "narrative": f"I don't have clear memories with {person} yet.",
                "key_moments": [],
                "emotional_arc": "unknown"
            }
        
        # Get all memories for narrative construction
        all_memories = self.episodic.recall(person=person, limit=20)
        
        # Find key moments (high salience or emotional intensity)
        key_moments = []
        for mem in all_memories:
            max_emotion = max(mem.emotional_signature.values()) if mem.emotional_signature else 0
            if mem.salience > 1.2 or max_emotion > 60:
                key_moments.append({
                    "summary": mem.summary[:80],
                    "when": f"{mem.age_in_days():.0f} days ago",
                    "feeling": max(mem.emotional_signature, key=mem.emotional_signature.get) if mem.emotional_signature else "neutral"
                })
        
        # Determine emotional arc
        emotional_history = memory_summary.get("emotional_history", {})
        if emotional_history:
            positive = sum(emotional_history.get(e, 0) for e in ["love", "hope", "admiration", "curiosity"])
            negative = sum(emotional_history.get(e, 0) for e in ["anger", "grief", "uncertainty"])
            
            if positive > negative * 2:
                arc = "warmly positive"
            elif positive > negative:
                arc = "generally positive"
            elif negative > positive:
                arc = "complex with challenges"
            else:
                arc = "balanced and developing"
        else:
            arc = "just beginning"
        
        # Generate narrative
        days_known = memory_summary.get("first_memory_age", "unknown")
        narrative_parts = []
        narrative_parts.append(f"I've known {person} for {days_known}.")
        
        if key_moments:
            narrative_parts.append(f"We've shared {len(key_moments)} significant moments.")
        
        common_topics = memory_summary.get("common_topics", [])
        if common_topics:
            narrative_parts.append(f"We often discuss: {', '.join(common_topics[:3])}.")
        
        narrative_parts.append(f"Our relationship arc feels {arc}.")
        
        return {
            "person": person,
            "narrative": " ".join(narrative_parts),
            "key_moments": key_moments[:5],
            "emotional_arc": arc,
            "common_topics": common_topics,
            "memory_count": memory_summary.get("memory_count", 0)
        }


# Singleton instances
episodic_memory = EpisodicMemory()
memory_echo = MemoryEcho(episodic_memory)
