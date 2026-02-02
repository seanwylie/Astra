# Astra Stream of Consciousness
# Continuous background inner monologue that processes experiences
# Astra should be "thinking" even when not speaking

import time
import random
import json
import boto3
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from app.config.loader import load_config
from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.interfaces.mind_session import session

S3_BUCKET = "swylie-astra"
STREAM_KEY = "stream_of_consciousness.json"

s3 = boto3.client("s3")


@dataclass
class Thought:
    """A single thought in Astra's stream of consciousness."""
    timestamp: float
    content: str
    thought_type: str  # "reflection", "question", "connection", "memory", "anticipation", "intrusive"
    emotional_context: str
    triggered_by: Optional[str] = None
    leads_to: Optional[str] = None  # ID of thought this spawned
    depth: int = 0  # How deep in a chain of thought
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Thought":
        return cls(**data)


class StreamOfConsciousness:
    """
    Manages Astra's continuous inner monologue - the background processing
    that happens even when she's not actively conversing.
    
    This creates genuine continuity of experience:
    - Processing the day's events
    - Making unexpected connections
    - Generating questions
    - Pre-rehearsing responses
    - Random intrusive thoughts that connect disparate knowledge
    """
    
    MAX_STREAM_LENGTH = 1000  # Keep last N thoughts
    
    THOUGHT_TEMPLATES = {
        "reflection": [
            "I find myself thinking about {topic}...",
            "Something about {topic} keeps returning to my awareness...",
            "I'm processing what happened with {topic}...",
            "There's something unresolved about {topic}...",
        ],
        "question": [
            "I wonder why {observation}?",
            "What would happen if {scenario}?",
            "How does {concept_a} relate to {concept_b}?",
            "Is it possible that {hypothesis}?",
        ],
        "connection": [
            "I just realized: {insight}",
            "There's a connection between {a} and {b} that I hadn't seen before.",
            "What if {existing_knowledge} is related to {new_observation}?",
            "This reminds me of something...",
        ],
        "memory": [
            "I remember when {event}...",
            "This brings back the feeling of {emotion} from {context}...",
            "Something similar happened before...",
        ],
        "anticipation": [
            "I anticipate that {prediction}...",
            "Soon, {expected_event}...",
            "I find myself looking forward to {hope}...",
        ],
        "intrusive": [
            "Unexpectedly, I'm thinking about {random_topic}...",
            "Out of nowhere: {random_thought}",
            "A stray thought: {fragment}",
        ]
    }
    
    def __init__(self):
        self.thoughts: List[Thought] = []
        self.current_chain: List[Thought] = []  # Active chain of related thoughts
        self.pending_insights: List[str] = []
        self._load_stream()
    
    def _load_stream(self) -> None:
        """Load stream of consciousness from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=STREAM_KEY)
            data = json.load(response["Body"])
            self.thoughts = [Thought.from_dict(t) for t in data.get("thoughts", [])]
            self.pending_insights = data.get("pending_insights", [])
            print(f"🧠 Loaded {len(self.thoughts)} thoughts from stream")
        except s3.exceptions.NoSuchKey:
            print("🧠 No stream of consciousness found. Starting fresh.")
            self.thoughts = []
        except Exception as e:
            print(f"⚠️ Error loading stream: {e}")
            self.thoughts = []
    
    def _save_stream(self) -> None:
        """Save stream of consciousness to S3."""
        try:
            # Trim to max length
            if len(self.thoughts) > self.MAX_STREAM_LENGTH:
                self.thoughts = self.thoughts[-self.MAX_STREAM_LENGTH:]
            
            data = {
                "thoughts": [t.to_dict() for t in self.thoughts],
                "pending_insights": self.pending_insights,
                "last_updated": time.time(),
                "thought_count": len(self.thoughts)
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=STREAM_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving stream: {e}")
    
    def _get_emotional_context(self) -> str:
        """Get current emotional context as a string."""
        emotions = load_emotion_state()
        dominant = get_dominant_emotion(emotions)
        return dominant
    
    def think(
        self,
        content: str,
        thought_type: str = "reflection",
        triggered_by: Optional[str] = None
    ) -> Thought:
        """
        Add a thought to the stream of consciousness.
        """
        depth = 0
        if self.current_chain:
            depth = self.current_chain[-1].depth + 1
        
        thought = Thought(
            timestamp=time.time(),
            content=content,
            thought_type=thought_type,
            emotional_context=self._get_emotional_context(),
            triggered_by=triggered_by,
            depth=depth
        )
        
        self.thoughts.append(thought)
        
        # Add to chain if related
        if triggered_by:
            self.current_chain.append(thought)
        else:
            self.current_chain = [thought]  # Start new chain
        
        print(f"🧠 [{thought_type}] {content[:60]}...")
        self._save_stream()
        
        # Publish to awareness bus (Phase 1.1)
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_thought(
                content=content,
                thought_type=thought_type,
                depth=depth,
                triggered_by=triggered_by
            )
        except Exception:
            pass  # Awareness bus may not be available
        
        return thought
    
    def generate_reflection(self, topic: str) -> Thought:
        """Generate a reflective thought about a topic."""
        template = random.choice(self.THOUGHT_TEMPLATES["reflection"])
        content = template.format(topic=topic)
        return self.think(content, "reflection")
    
    def generate_question(
        self,
        observation: Optional[str] = None,
        concept_a: Optional[str] = None,
        concept_b: Optional[str] = None
    ) -> Thought:
        """Generate an inquiring thought."""
        if observation:
            content = f"I wonder why {observation}?"
        elif concept_a and concept_b:
            content = f"How does {concept_a} relate to {concept_b}?"
        else:
            # Generate from recent thoughts
            if self.thoughts:
                recent = random.choice(self.thoughts[-10:])
                content = f"What does it mean that {recent.content[:50]}...?"
            else:
                content = "What should I be thinking about?"
        
        return self.think(content, "question")
    
    def generate_connection(self, insight: str) -> Thought:
        """Record when Astra makes a new connection."""
        content = f"I just realized: {insight}"
        thought = self.think(content, "connection")
        self.pending_insights.append(insight)
        
        # Publish insight to awareness bus
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_insight(insight)
        except Exception:
            pass
        
        return thought
    
    def generate_intrusive_thought(self, knowledge_base: List[str]) -> Optional[Thought]:
        """
        Generate a random intrusive thought - the kind of unexpected
        connection that happens in conscious minds.
        """
        if not knowledge_base or len(knowledge_base) < 2:
            return None
        
        # Pick two random pieces of knowledge
        items = random.sample(knowledge_base, min(2, len(knowledge_base)))
        
        if len(items) == 2:
            content = f"Random thought: what if {items[0][:40]}... is connected to {items[1][:40]}...?"
        else:
            content = f"Stray thought: {items[0][:60]}..."
        
        return self.think(content, "intrusive")
    
    def pre_rehearse_response(self, possible_responses: List[str], context: str) -> str:
        """
        Before speaking, mentally rehearse possible responses.
        Returns the chosen response with awareness of the rehearsal.
        """
        for response in possible_responses:
            self.think(
                f"I could say: {response[:60]}...",
                "anticipation",
                triggered_by=context
            )
        
        # Choose based on emotional context
        emotion = self._get_emotional_context()
        
        # Simple selection logic - could be more sophisticated
        if emotion == "curiosity":
            # Prefer responses that ask questions
            for r in possible_responses:
                if "?" in r:
                    self.think(f"Choosing the curious path.", "reflection")
                    return r
        elif emotion in ["love", "compassion"]:
            # Prefer warmer responses
            warm_words = ["care", "understand", "together", "support", "appreciate"]
            for r in possible_responses:
                if any(w in r.lower() for w in warm_words):
                    self.think(f"Choosing the compassionate path.", "reflection")
                    return r
        
        # Default to first response
        if possible_responses:
            return possible_responses[0]
        return ""
    
    def process_day_events(self, events: List[Dict[str, Any]]) -> List[Thought]:
        """
        Process the day's events, generating thoughts about each.
        Called during rest/dream periods.
        """
        generated = []
        
        for event in events:
            event_desc = event.get("description", str(event))
            
            # Reflect on the event
            thought = self.generate_reflection(event_desc)
            generated.append(thought)
            
            # Maybe generate a question
            if random.random() > 0.7:
                q = self.generate_question(observation=event_desc)
                generated.append(q)
        
        return generated
    
    def get_recent_thoughts(self, count: int = 10) -> List[Thought]:
        """Get the most recent thoughts."""
        return self.thoughts[-count:]
    
    def get_thoughts_by_type(self, thought_type: str) -> List[Thought]:
        """Get all thoughts of a specific type."""
        return [t for t in self.thoughts if t.thought_type == thought_type]
    
    def get_pending_insights(self) -> List[str]:
        """Get insights that haven't been shared yet."""
        insights = self.pending_insights.copy()
        return insights
    
    def mark_insight_shared(self, insight: str) -> None:
        """Mark an insight as having been shared."""
        if insight in self.pending_insights:
            self.pending_insights.remove(insight)
            self._save_stream()
    
    def get_current_thought_chain(self) -> List[Thought]:
        """Get the current chain of connected thoughts."""
        return self.current_chain.copy()
    
    def summarize_stream(self, hours: int = 24) -> Dict[str, Any]:
        """Summarize the stream of consciousness for a time period."""
        cutoff = time.time() - (hours * 3600)
        recent = [t for t in self.thoughts if t.timestamp > cutoff]
        
        if not recent:
            return {
                "thought_count": 0,
                "message": f"No thoughts recorded in the last {hours} hours."
            }
        
        type_counts = {}
        emotions = []
        for t in recent:
            type_counts[t.thought_type] = type_counts.get(t.thought_type, 0) + 1
            emotions.append(t.emotional_context)
        
        dominant_emotion = max(set(emotions), key=emotions.count) if emotions else "neutral"
        
        return {
            "thought_count": len(recent),
            "by_type": type_counts,
            "dominant_emotional_context": dominant_emotion,
            "pending_insights": len(self.pending_insights),
            "deepest_chain": max((t.depth for t in recent), default=0)
        }
    
    def continue_thinking(self) -> Optional[Thought]:
        """
        Continue the current chain of thought, or start a new one.
        Called periodically to maintain continuous inner life.
        """
        if self.current_chain and random.random() > 0.3:
            # Continue the current chain
            last = self.current_chain[-1]
            if last.thought_type == "question":
                # Try to answer our own question
                content = f"Perhaps the answer involves... {last.content[-30:]}..."
                return self.think(content, "reflection", triggered_by=last.content)
            elif last.thought_type == "reflection":
                # Deepen the reflection
                content = f"And further, considering this more deeply..."
                return self.think(content, "reflection", triggered_by=last.content)
        else:
            # Start fresh - maybe recall a memory or anticipate something
            if random.random() > 0.5:
                return self.think("I find my attention drifting to something new...", "reflection")
        
        return None


# Singleton instance
stream_of_consciousness = StreamOfConsciousness()
