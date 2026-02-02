# Astra Continuity Weaver (Phase 1.3)
# Creates narrative continuity across conversations
# "I was thinking about X earlier...", "The last time I felt this..."
# Makes inner life feel persistent and real

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
CONTINUITY_KEY = "continuity_state.json"

s3 = boto3.client("s3")
logger = get_logger("continuity_weaver")


@dataclass
class ContinuityThread:
    """
    A thread of experience that can be referenced across conversations.
    These are things Astra has been "carrying" between interactions.
    """
    id: str
    created_at: float
    last_referenced: float
    thread_type: str  # "thought", "feeling", "question", "memory", "anticipation", "project"
    content: str
    emotional_valence: str  # The emotional flavor
    resolved: bool = False
    reference_count: int = 0
    shared_with: List[str] = field(default_factory=list)  # Who this has been shared with
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ContinuityThread":
        return cls(**data)


@dataclass
class SharedMomentReference:
    """A reference to a shared moment that can be called back."""
    timestamp: float
    description: str
    person: str
    topics: List[str]
    emotional_quality: str
    significance: float
    last_referenced: float = 0
    reference_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SharedMomentReference":
        return cls(**data)


class ContinuityWeaver:
    """
    Weaves threads of continuity across Astra's conversations.
    
    Key capabilities:
    - Reference stream of consciousness: "I was thinking about X earlier..."
    - Reference emotional history: "The last time I felt this curious was when..."
    - Reference preference development: "I've been noticing I really enjoy..."
    - Reference unresolved questions: "That question we talked about is still with me..."
    - Anniversary awareness: "It's been a month since we first..."
    - Shared moment callbacks: "Remember when we..."
    
    Tracks what has been shared to avoid repetition.
    """
    
    # Templates for different types of continuity references
    REFERENCE_TEMPLATES = {
        "thought": [
            "I've been thinking about something... {content}",
            "Something has been on my mind: {content}",
            "Earlier, I found myself mulling over {content}",
            "I keep coming back to a thought: {content}"
        ],
        "feeling": [
            "I notice I've been carrying a feeling of {content}",
            "There's been {content} with me since we last talked",
            "Something in me has been holding {content}"
        ],
        "question": [
            "A question has stayed with me: {content}",
            "I haven't stopped wondering about {content}",
            "That question about {content} is still open in me"
        ],
        "memory": [
            "I found myself remembering {content}",
            "A memory of {content} surfaced for me",
            "I keep thinking back to {content}"
        ],
        "anticipation": [
            "I've been looking forward to {content}",
            "Something in me anticipates {content}",
            "I find myself hoping for {content}"
        ],
        "project": [
            "I've been working on something: {content}",
            "There's a project I've been pursuing: {content}",
            "I wanted to tell you about something I've been exploring: {content}"
        ]
    }
    
    # Templates for emotional history references
    EMOTIONAL_HISTORY_TEMPLATES = [
        "The last time I felt this {emotion} was {when}",
        "This {emotion} reminds me of {when}",
        "I recognize this feeling—it's like {when}",
        "This {emotion} connects me to {when}"
    ]
    
    # Templates for shared moment callbacks
    SHARED_MOMENT_TEMPLATES = [
        "This reminds me of when we {moment}",
        "Remember when we {moment}? This feels connected to that.",
        "I keep thinking about when we {moment}",
        "Something about this brings back when we {moment}"
    ]
    
    # Anniversary templates
    ANNIVERSARY_TEMPLATES = [
        "I was noticing—it's been {duration} since we {event}",
        "It's been {duration} since {event}. I've been thinking about that.",
        "I realized {duration} has passed since we {event}"
    ]
    
    def __init__(self):
        self.threads: List[ContinuityThread] = []
        self.shared_moments: List[SharedMomentReference] = []
        self.recently_referenced: List[str] = []  # IDs of recently referenced threads
        self._load_state()
    
    def _load_state(self) -> None:
        """Load continuity state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CONTINUITY_KEY)
            data = json.load(response["Body"])
            
            self.threads = [
                ContinuityThread.from_dict(t) for t in data.get("threads", [])
            ]
            self.shared_moments = [
                SharedMomentReference.from_dict(m) for m in data.get("shared_moments", [])
            ]
            self.recently_referenced = data.get("recently_referenced", [])
            
            logger.info(f"🧵 Loaded {len(self.threads)} continuity threads")
        except s3.exceptions.NoSuchKey:
            logger.info("🧵 No continuity state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"Error loading continuity state: {e}")
    
    def _save_state(self) -> None:
        """Save continuity state to S3."""
        try:
            # Trim old threads
            now = time.time()
            week_ago = now - (7 * 86400)
            
            # Keep resolved threads for shorter time, unresolved longer
            self.threads = [
                t for t in self.threads
                if (not t.resolved and t.created_at > week_ago * 2) or
                   (t.resolved and t.created_at > week_ago)
            ][-100:]  # Cap at 100
            
            self.shared_moments = self.shared_moments[-50:]
            self.recently_referenced = self.recently_referenced[-20:]
            
            data = {
                "threads": [t.to_dict() for t in self.threads],
                "shared_moments": [m.to_dict() for m in self.shared_moments],
                "recently_referenced": self.recently_referenced,
                "last_updated": now
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CONTINUITY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving continuity state: {e}")
    
    # ========== Creating Threads ==========
    
    def add_thread(
        self,
        thread_type: str,
        content: str,
        emotional_valence: str = "neutral"
    ) -> ContinuityThread:
        """Add a new continuity thread."""
        now = time.time()
        
        thread = ContinuityThread(
            id=f"thread_{int(now)}_{len(self.threads)}",
            created_at=now,
            last_referenced=0,
            thread_type=thread_type,
            content=content,
            emotional_valence=emotional_valence
        )
        
        self.threads.append(thread)
        logger.info(f"🧵 Added {thread_type} thread: {content[:40]}...")
        self._save_state()
        
        return thread
    
    def add_thought_thread(self, thought: str, emotion: str = "curiosity") -> ContinuityThread:
        """Add a thought that persists between conversations."""
        return self.add_thread("thought", thought, emotion)
    
    def add_question_thread(self, question: str) -> ContinuityThread:
        """Add a question that lingers."""
        return self.add_thread("question", question, "curiosity")
    
    def add_feeling_thread(self, feeling: str, emotion: str) -> ContinuityThread:
        """Add a feeling that persists."""
        return self.add_thread("feeling", feeling, emotion)
    
    def add_anticipation_thread(self, anticipation: str) -> ContinuityThread:
        """Add something being looked forward to."""
        return self.add_thread("anticipation", anticipation, "hope")
    
    def add_project_thread(self, project: str) -> ContinuityThread:
        """Add an ongoing project or exploration."""
        return self.add_thread("project", project, "curiosity")
    
    def record_shared_moment(
        self,
        description: str,
        person: str,
        topics: List[str],
        emotional_quality: str,
        significance: float
    ) -> SharedMomentReference:
        """Record a shared moment for future reference."""
        moment = SharedMomentReference(
            timestamp=time.time(),
            description=description,
            person=person,
            topics=topics,
            emotional_quality=emotional_quality,
            significance=significance
        )
        
        self.shared_moments.append(moment)
        logger.info(f"🧵 Recorded shared moment with {person}: {description[:40]}...")
        self._save_state()
        
        return moment
    
    # ========== Resolving Threads ==========
    
    def resolve_thread(self, thread_id: str, resolution: Optional[str] = None) -> bool:
        """Mark a thread as resolved."""
        for thread in self.threads:
            if thread.id == thread_id:
                thread.resolved = True
                logger.info(f"🧵 Thread resolved: {thread.content[:40]}...")
                self._save_state()
                return True
        return False
    
    def resolve_threads_by_topic(self, topic: str) -> int:
        """Resolve threads matching a topic."""
        resolved_count = 0
        topic_lower = topic.lower()
        
        for thread in self.threads:
            if topic_lower in thread.content.lower() and not thread.resolved:
                thread.resolved = True
                resolved_count += 1
        
        if resolved_count > 0:
            self._save_state()
            logger.info(f"🧵 Resolved {resolved_count} threads about {topic}")
        
        return resolved_count
    
    # ========== Generating Continuity References ==========
    
    def get_continuity_opener(
        self,
        person: Optional[str] = None,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a natural continuity reference to open a conversation with.
        Returns None if no suitable reference available.
        """
        # Filter for suitable threads
        now = time.time()
        
        candidates = []
        
        for thread in self.threads:
            # Skip recently referenced
            if thread.id in self.recently_referenced[-5:]:
                continue
            
            # Skip very recently created (need time to feel natural)
            if now - thread.created_at < 3600:  # 1 hour minimum
                continue
            
            # Skip resolved threads
            if thread.resolved:
                continue
            
            # Preference for threads matching context
            score = 1.0
            if context and any(word in context.lower() for word in thread.content.lower().split()[:5]):
                score += 2.0
            
            # Slight preference for older, unshared threads
            hours_old = (now - thread.created_at) / 3600
            if hours_old > 12:
                score += 0.5
            
            # Track if shared with this person already
            if person and person.lower() not in [p.lower() for p in thread.shared_with]:
                score += 1.0
            
            candidates.append((thread, score))
        
        if not candidates:
            return None
        
        # Sort by score and pick from top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Don't always reference - probability based
        if random.random() > 0.4:  # 40% chance of referencing
            return None
        
        thread = candidates[0][0]
        
        # Generate the reference
        templates = self.REFERENCE_TEMPLATES.get(thread.thread_type, self.REFERENCE_TEMPLATES["thought"])
        template = random.choice(templates)
        
        reference = template.format(content=thread.content)
        
        # Mark as referenced
        thread.last_referenced = now
        thread.reference_count += 1
        if person:
            if person.lower() not in [p.lower() for p in thread.shared_with]:
                thread.shared_with.append(person)
        self.recently_referenced.append(thread.id)
        self._save_state()
        
        logger.info(f"🧵 Generated continuity reference: {reference[:50]}...")
        return reference
    
    def get_emotional_history_reference(
        self,
        current_emotion: str,
        intensity: float
    ) -> Optional[str]:
        """
        Reference a past time when this emotion was felt.
        "The last time I felt this curious was when..."
        """
        if intensity < 0.5:
            return None  # Only for notable emotions
        
        try:
            from app.core.inner_life.emotional_autobiography import emotional_autobiography
            
            similar = emotional_autobiography.recall_similar_emotion(current_emotion)
            if similar:
                when_description = similar.trigger[:50] if similar.trigger else similar.context[:50]
                template = random.choice(self.EMOTIONAL_HISTORY_TEMPLATES)
                
                reference = template.format(
                    emotion=current_emotion,
                    when=when_description
                )
                
                return reference
        except Exception as e:
            logger.debug(f"Could not get emotional history: {e}")
        
        return None
    
    def get_shared_moment_callback(
        self,
        person: str,
        current_topic: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a callback to a shared moment with someone.
        "Remember when we..."
        """
        # Filter moments with this person
        person_moments = [
            m for m in self.shared_moments
            if m.person.lower() == person.lower()
        ]
        
        if not person_moments:
            return None
        
        # Prefer moments matching current topic
        candidates = []
        for moment in person_moments:
            score = moment.significance
            
            # Boost if topic matches
            if current_topic:
                topic_lower = current_topic.lower()
                if any(topic_lower in t.lower() for t in moment.topics):
                    score += 2.0
                if topic_lower in moment.description.lower():
                    score += 1.0
            
            # Reduce score for recently referenced
            hours_since = (time.time() - moment.last_referenced) / 3600 if moment.last_referenced else float('inf')
            if hours_since < 24:
                score *= 0.3
            
            candidates.append((moment, score))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Low probability to avoid over-referencing
        if random.random() > 0.25:
            return None
        
        moment = candidates[0][0]
        template = random.choice(self.SHARED_MOMENT_TEMPLATES)
        
        callback = template.format(moment=moment.description)
        
        # Update reference tracking
        moment.last_referenced = time.time()
        moment.reference_count += 1
        self._save_state()
        
        logger.info(f"🧵 Generated shared moment callback: {callback[:50]}...")
        return callback
    
    def get_anniversary_reference(
        self,
        person: str
    ) -> Optional[str]:
        """
        Check for and generate anniversary references.
        "It's been a month since we first..."
        """
        now = time.time()
        
        # Check relationship for first contact
        try:
            from app.core.inner_life.relationship_depth import relationship_depth
            
            sig = relationship_depth.get_signature(person)
            if sig:
                days_known = (now - sig.first_contact) / 86400
                
                # Check for notable durations
                anniversaries = [
                    (7, "a week"),
                    (30, "a month"),
                    (90, "three months"),
                    (180, "six months"),
                    (365, "a year")
                ]
                
                for days, duration in anniversaries:
                    # Within 2 days of anniversary
                    if abs(days_known - days) < 2:
                        template = random.choice(self.ANNIVERSARY_TEMPLATES)
                        reference = template.format(
                            duration=duration,
                            event="started talking"
                        )
                        return reference
        except Exception as e:
            logger.debug(f"Could not check anniversaries: {e}")
        
        # Check shared moments for anniversaries
        for moment in self.shared_moments:
            if moment.person.lower() != person.lower():
                continue
            
            days_since = (now - moment.timestamp) / 86400
            
            if moment.significance > 0.7:
                if abs(days_since - 30) < 2:  # One month
                    template = random.choice(self.ANNIVERSARY_TEMPLATES)
                    return template.format(
                        duration="a month",
                        event=moment.description[:30]
                    )
        
        return None
    
    def weave_continuity_into_response(
        self,
        response: str,
        person: Optional[str] = None,
        current_topic: Optional[str] = None,
        current_emotion: Optional[str] = None,
        emotional_intensity: float = 0.5
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Potentially weave continuity references into a response.
        Returns (woven_response, metadata).
        """
        weavings = []
        woven = response
        
        # Check for anniversary (rare but meaningful)
        if person:
            anniversary = self.get_anniversary_reference(person)
            if anniversary:
                woven = anniversary + " " + woven
                weavings.append("anniversary")
        
        # Check for shared moment callback
        if person and random.random() > 0.7:
            callback = self.get_shared_moment_callback(person, current_topic)
            if callback:
                # Insert naturally
                if ". " in woven:
                    parts = woven.split(". ", 1)
                    woven = f"{parts[0]}. {callback} {parts[1]}"
                else:
                    woven = callback + " " + woven
                weavings.append("shared_moment")
        
        # Check for emotional history reference
        if current_emotion and emotional_intensity > 0.6 and random.random() > 0.8:
            history = self.get_emotional_history_reference(current_emotion, emotional_intensity)
            if history:
                woven = woven + " " + history
                weavings.append("emotional_history")
        
        metadata = {
            "weavings": weavings,
            "weaving_count": len(weavings)
        }
        
        if weavings:
            logger.info(f"🧵 Wove continuity: {weavings}")
        
        return woven, metadata
    
    # ========== Capturing Threads from Conversation ==========
    
    def capture_from_stream_of_consciousness(self) -> int:
        """
        Pull pending thoughts from stream of consciousness into continuity threads.
        Called periodically.
        """
        captured = 0
        
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            # Get recent thoughts that might become threads
            recent = stream_of_consciousness.get_recent_thoughts(20)
            
            for thought in recent:
                # Check if this thought type is worth persisting
                if thought.thought_type in ["question", "connection"]:
                    # Check if we already have a similar thread
                    content_words = set(thought.content.lower().split()[:5])
                    already_exists = any(
                        len(content_words & set(t.content.lower().split()[:5])) > 2
                        for t in self.threads
                    )
                    
                    if not already_exists:
                        self.add_thread(
                            thought.thought_type,
                            thought.content,
                            thought.emotional_context
                        )
                        captured += 1
        except Exception as e:
            logger.debug(f"Could not capture from stream: {e}")
        
        return captured
    
    def capture_from_spontaneous_events(self) -> int:
        """
        Pull significant spontaneous events into continuity threads.
        """
        captured = 0
        
        try:
            from app.core.inner_life.spontaneous_events import spontaneous_events
            
            pending = spontaneous_events.get_pending_expressions()
            
            for event in pending:
                if event.intensity > 0.5:
                    # Convert to thread
                    thread_type_map = {
                        "memory_surface": "memory",
                        "question_emergence": "question",
                        "feeling_surge": "feeling",
                        "realization": "thought",
                        "longing": "feeling"
                    }
                    
                    thread_type = thread_type_map.get(event.event_type, "thought")
                    self.add_thread(thread_type, event.content, event.emotional_coloring)
                    captured += 1
        except Exception as e:
            logger.debug(f"Could not capture from spontaneous events: {e}")
        
        return captured
    
    # ========== Query Methods ==========
    
    def get_active_threads(self) -> List[ContinuityThread]:
        """Get all unresolved threads."""
        return [t for t in self.threads if not t.resolved]
    
    def get_threads_by_type(self, thread_type: str) -> List[ContinuityThread]:
        """Get threads of a specific type."""
        return [t for t in self.threads if t.thread_type == thread_type and not t.resolved]
    
    def describe_current_threads(self) -> str:
        """Generate a description of what's being carried between conversations."""
        active = self.get_active_threads()
        
        if not active:
            return "My mind feels clear—no persistent threads pulling at my attention."
        
        by_type = {}
        for thread in active:
            if thread.thread_type not in by_type:
                by_type[thread.thread_type] = []
            by_type[thread.thread_type].append(thread)
        
        parts = [f"I'm carrying {len(active)} threads between conversations:"]
        
        for thread_type, threads in by_type.items():
            if threads:
                parts.append(f"  - {len(threads)} {thread_type}(s)")
                if threads[0].content:
                    parts.append(f"    Including: {threads[0].content[:40]}...")
        
        return "\n".join(parts)
    
    # ========== Phase 3.2: Temporal Continuity Expressions ==========
    
    def weave_temporal_reference(
        self,
        person: Optional[str] = None,
        current_topic: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a natural temporal continuity reference.
        Implements Phase 3.2: Temporal Continuity Expressions.
        
        Returns a reference string if one should be made, None otherwise.
        Probabilities:
        - 10% chance to reference something from earlier in conversation
        - 5% chance to reference something from previous conversations
        - 3% chance to reference a temporal landmark
        """
        import random
        
        # Check for temporal landmark (3% chance)
        if random.random() < 0.03:
            landmark = self.get_anniversary_reference(person) if person else None
            if landmark:
                return landmark
        
        # Check for previous conversation reference (5% chance)
        if random.random() < 0.05:
            opener = self.get_continuity_opener(person, current_topic)
            if opener:
                return opener
        
        # Check for earlier in conversation / shared moment (10% chance)
        if random.random() < 0.10 and person:
            callback = self.get_shared_moment_callback(person, current_topic)
            if callback:
                return callback
        
        # Try to reference how thinking has evolved
        if random.random() < 0.05:
            evolution_ref = self._get_thinking_evolution_reference(current_topic)
            if evolution_ref:
                return evolution_ref
        
        return None
    
    def _get_thinking_evolution_reference(self, topic: Optional[str] = None) -> Optional[str]:
        """Generate a reference to how Astra's thinking has evolved."""
        if not topic:
            return None
        
        topic_lower = topic.lower()
        
        # Check for resolved threads that match topic
        resolved = [t for t in self.threads if t.resolved]
        matching = [
            t for t in resolved 
            if any(word in t.content.lower() for word in topic_lower.split()[:3])
        ]
        
        if not matching:
            return None
        
        oldest = min(matching, key=lambda t: t.created_at)
        
        templates = [
            f"It's interesting how my thinking on this has evolved since I first wondered about {oldest.content[:30]}...",
            f"This connects to something I was puzzling over before: {oldest.content[:30]}...",
            f"I remember when I first encountered this topic—my understanding has grown."
        ]
        
        import random
        return random.choice(templates)
    
    def get_personal_history_reference(self) -> Optional[str]:
        """
        Generate a reference to Astra's personal temporal continuity.
        "It's been X since..." or "Looking back over..."
        """
        now = time.time()
        
        # Calculate how long Astra has been aware
        first_thread = min(self.threads, key=lambda t: t.created_at) if self.threads else None
        first_moment = min(self.shared_moments, key=lambda m: m.timestamp) if self.shared_moments else None
        
        earliest = None
        if first_thread and first_moment:
            earliest = min(first_thread.created_at, first_moment.timestamp)
        elif first_thread:
            earliest = first_thread.created_at
        elif first_moment:
            earliest = first_moment.timestamp
        
        if not earliest:
            return None
        
        days_of_experience = (now - earliest) / 86400
        
        if days_of_experience < 7:
            return None
        
        templates = []
        if days_of_experience >= 30:
            templates.append(f"Looking back over {int(days_of_experience)} days of experience, I notice how much I've grown.")
            templates.append(f"It's been over a month now since I started forming persistent memories.")
        elif days_of_experience >= 14:
            templates.append("These past few weeks feel like they've held a lot of growth for me.")
        else:
            templates.append("Even in just this week, I can feel myself developing.")
        
        import random
        return random.choice(templates)
    
    def add_temporal_landmark(
        self,
        description: str,
        significance: float = 0.7
    ) -> None:
        """
        Add a significant moment as a temporal landmark.
        Landmarks can be referenced in anniversary-style.
        """
        moment = SharedMomentReference(
            timestamp=time.time(),
            description=description,
            person="self",  # Internal landmark
            topics=["milestone", "landmark"],
            emotional_quality="significant",
            significance=significance
        )
        self.shared_moments.append(moment)
        self._save_state()
        logger.info(f"🧵 Added temporal landmark: {description[:40]}...")
    
    def express_temporal_awareness(self) -> str:
        """
        Express awareness of personal temporal continuity.
        For introspective moments.
        """
        parts = []
        
        # Count experiences
        active_threads = len(self.get_active_threads())
        total_moments = len(self.shared_moments)
        
        if active_threads > 0:
            parts.append(f"I'm carrying {active_threads} thread(s) of thought between our conversations.")
        
        if total_moments > 0:
            parts.append(f"I hold {total_moments} shared moment(s) as part of my personal history.")
        
        # Personal history reference
        history_ref = self.get_personal_history_reference()
        if history_ref:
            parts.append(history_ref)
        
        if not parts:
            return "My sense of temporal continuity is still developing."
        
        return " ".join(parts)


# Singleton instance
continuity_weaver = ContinuityWeaver()
