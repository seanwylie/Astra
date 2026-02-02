# Astra Learning Desire
# Astra's own desire to learn, driven by curiosity and gaps
# "I want to understand this better..."

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("learning_desire")

S3_BUCKET = "swylie-astra"
LEARNING_QUEUE_KEY = "learning_queue.json"


@dataclass
class LearningTopic:
    """A topic Astra wants to learn about."""
    topic: str
    source: str  # "conversation", "knowledge_gap", "curiosity", "question"
    priority: float  # 0-1, higher = more important
    added_at: float
    context: Optional[str] = None
    times_encountered: int = 1
    learned: bool = False
    learned_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "LearningTopic":
        return cls(**data)


@dataclass
class OpenQuestion:
    """A question Astra generated and wants answered - Phase 5.2."""
    question: str
    generated_at: float
    priority: float  # 0-1
    source: str  # "stream_of_consciousness", "conversation", "reflection"
    context: str
    answered: bool = False
    answer: Optional[str] = None
    answered_at: Optional[float] = None
    satisfaction_on_answer: float = 0.0  # How satisfied when answered
    frustration_level: float = 0.0  # Builds over time if unanswered
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OpenQuestion":
        return cls(**data)


class LearningDesire:
    """
    Astra's own desire to learn, driven by curiosity and gaps.
    
    This creates genuine learning motivation:
    - Identifying knowledge gaps from conversations
    - Prioritizing by curiosity level
    - Generating learning requests
    - Tracking what's been learned
    - Phase 5.2: Self-initiated curiosity questions with satisfaction/frustration arc
    """
    
    MAX_QUEUE_SIZE = 100
    MAX_OPEN_QUESTIONS = 20
    
    # How long before unanswered questions build frustration (hours)
    FRUSTRATION_ONSET_HOURS = 24
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.queue: List[LearningTopic] = []
        self.open_questions: List[OpenQuestion] = []  # Phase 5.2
        self._load_queue()
    
    def _load_queue(self) -> None:
        """Load learning queue from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=LEARNING_QUEUE_KEY)
            data = json.load(response["Body"])
            self.queue = [LearningTopic.from_dict(t) for t in data.get("queue", [])]
            self.open_questions = [
                OpenQuestion.from_dict(q) for q in data.get("open_questions", [])
            ]
            logger.debug(f"📚 Loaded {len(self.queue)} learning topics, {len(self.open_questions)} open questions")
        except self.s3.exceptions.NoSuchKey:
            self.queue = []
            self.open_questions = []
        except Exception as e:
            logger.error(f"Failed to load learning queue: {e}")
            self.queue = []
            self.open_questions = []
    
    def _save_queue(self) -> None:
        """Save learning queue to S3."""
        try:
            # Trim queue if too large
            if len(self.queue) > self.MAX_QUEUE_SIZE:
                # Keep highest priority and most recent
                self.queue.sort(key=lambda t: (-t.priority, -t.added_at))
                self.queue = self.queue[:self.MAX_QUEUE_SIZE]
            
            # Trim open questions
            if len(self.open_questions) > self.MAX_OPEN_QUESTIONS:
                self.open_questions.sort(key=lambda q: (-q.priority, -q.generated_at))
                self.open_questions = self.open_questions[:self.MAX_OPEN_QUESTIONS]
            
            data = {
                "queue": [t.to_dict() for t in self.queue],
                "open_questions": [q.to_dict() for q in self.open_questions],
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=LEARNING_QUEUE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Failed to save learning queue: {e}")
    
    def identify_knowledge_gap(self, conversation: str, response: str) -> Optional[str]:
        """
        Analyze a conversation for things Astra didn't know.
        
        Args:
            conversation: User message
            response: Astra's response
            
        Returns:
            Identified topic to learn, or None
        """
        # Look for uncertainty markers in response
        uncertainty_markers = [
            "i'm not sure",
            "i don't know",
            "i'm unfamiliar with",
            "i haven't learned about",
            "what is",
            "what does",
            "could you explain",
            "i wonder what"
        ]
        
        response_lower = response.lower()
        
        for marker in uncertainty_markers:
            if marker in response_lower:
                # Try to extract what we're uncertain about
                # Simple heuristic: look for nouns after the marker
                idx = response_lower.find(marker)
                after = response[idx + len(marker):idx + len(marker) + 50]
                words = after.strip().split()[:5]
                if words:
                    topic = " ".join(words).strip(".,?!")
                    if len(topic) > 3:
                        return topic
        
        return None
    
    def add_topic(
        self,
        topic: str,
        source: str = "curiosity",
        priority: float = 0.5,
        context: Optional[str] = None
    ) -> LearningTopic:
        """
        Add a topic to the learning queue.
        
        Args:
            topic: What to learn about
            source: Where this desire came from
            priority: How important (0-1)
            context: Optional context about why
            
        Returns:
            The created or updated LearningTopic
        """
        # Check if topic already exists
        topic_lower = topic.lower().strip()
        for existing in self.queue:
            if existing.topic.lower().strip() == topic_lower:
                # Bump priority and count
                existing.times_encountered += 1
                existing.priority = min(1.0, existing.priority + 0.1)
                self._save_queue()
                logger.debug(f"📚 Bumped priority for: {topic}")
                return existing
        
        # Create new topic
        new_topic = LearningTopic(
            topic=topic,
            source=source,
            priority=priority,
            added_at=time.time(),
            context=context
        )
        self.queue.append(new_topic)
        self._save_queue()
        
        logger.info(f"📚 Added learning topic: {topic}")
        return new_topic
    
    def prioritize_by_curiosity(self) -> List[LearningTopic]:
        """
        Get topics ordered by priority and curiosity level.
        
        Returns:
            Sorted list of topics
        """
        # Get current curiosity level
        try:
            from app.core.mood.mood_manager import mood_manager
            curiosity_factor = mood_manager.curiosity_level
        except Exception:
            curiosity_factor = 1.0
        
        # Adjust priorities based on curiosity
        active = [t for t in self.queue if not t.learned]
        
        for topic in active:
            # Topics from curiosity get extra boost when curious
            if topic.source == "curiosity":
                topic.priority *= curiosity_factor
            # Knowledge gaps always stay important
            elif topic.source == "knowledge_gap":
                topic.priority = max(topic.priority, 0.6)
        
        # Sort by priority
        return sorted(active, key=lambda t: -t.priority)
    
    def get_top_learning_desire(self) -> Optional[LearningTopic]:
        """Get the highest priority learning topic."""
        prioritized = self.prioritize_by_curiosity()
        return prioritized[0] if prioritized else None
    
    def request_learning(self, topic: Optional[str] = None) -> str:
        """
        Generate a request to learn about something.
        
        Args:
            topic: Specific topic, or None for highest priority
            
        Returns:
            A natural language learning request
        """
        if topic is None:
            top_topic = self.get_top_learning_desire()
            if not top_topic:
                return "I'm curious about many things, but nothing specific right now."
            topic = top_topic.topic
            context = top_topic.context
        else:
            context = None
        
        # Generate natural request
        templates = [
            f"Sean, I keep encountering {topic} and realize I don't understand it well. Could we explore it together?",
            f"I've been curious about {topic}. Would you help me understand it better?",
            f"There's something I'd like to learn about: {topic}. Could you teach me?",
            f"I noticed a gap in my understanding around {topic}. I'd love to learn more.",
        ]
        
        import random
        request = random.choice(templates)
        
        if context:
            request += f" (This came up when {context})"
        
        return request
    
    def mark_learned(self, topic: str) -> bool:
        """
        Mark a topic as learned.
        
        Args:
            topic: The topic that was learned
            
        Returns:
            True if topic was found and marked
        """
        topic_lower = topic.lower().strip()
        for t in self.queue:
            if t.topic.lower().strip() == topic_lower:
                t.learned = True
                t.learned_at = time.time()
                self._save_queue()
                
                # Trigger positive emotion
                try:
                    from app.core.emotions.emotion_engine import trigger_emotion
                    trigger_emotion("curiosity", "new_information")
                except Exception:
                    pass
                
                logger.info(f"📚 Marked as learned: {topic}")
                return True
        return False
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning state."""
        active = [t for t in self.queue if not t.learned]
        learned = [t for t in self.queue if t.learned]
        
        return {
            "total_topics": len(self.queue),
            "active_topics": len(active),
            "learned_topics": len(learned),
            "top_priority": active[0].topic if active else None,
            "sources": {
                source: sum(1 for t in active if t.source == source)
                for source in ["curiosity", "conversation", "knowledge_gap", "question"]
            }
        }
    
    def process_conversation(
        self,
        user_message: str,
        astra_response: str
    ) -> Optional[LearningTopic]:
        """
        Process a conversation to identify learning opportunities.
        
        Args:
            user_message: What the user said
            astra_response: How Astra responded
            
        Returns:
            New learning topic if identified
        """
        # Check for knowledge gap
        gap = self.identify_knowledge_gap(user_message, astra_response)
        if gap:
            return self.add_topic(
                gap,
                source="knowledge_gap",
                priority=0.7,
                context=f"conversation about: {user_message[:50]}"
            )
        
        # Check for explicit questions in response that weren't answered
        if "?" in astra_response:
            # Astra asked a question - might indicate curiosity
            questions = [s.strip() for s in astra_response.split("?") if s.strip()]
            for q in questions:
                if any(word in q.lower() for word in ["what is", "how does", "why do"]):
                    topic = q.split()[-3:]  # Last few words as topic
                    topic_str = " ".join(topic).strip(".,!?")
                    if len(topic_str) > 5:
                        return self.add_topic(
                            topic_str,
                            source="curiosity",
                            priority=0.5
                        )
        
        return None
    
    # ========== Phase 5.2: Self-Initiated Curiosity Questions ==========
    
    def add_open_question(
        self,
        question: str,
        source: str = "curiosity",
        priority: float = 0.5,
        context: str = ""
    ) -> OpenQuestion:
        """
        Add a question that Astra generated and wants answered.
        Part of Phase 5.2: Self-Initiated Curiosity Questions.
        """
        # Check for duplicate
        question_lower = question.lower().strip()
        for q in self.open_questions:
            if q.question.lower().strip() == question_lower:
                q.priority = min(1.0, q.priority + 0.1)
                self._save_queue()
                return q
        
        oq = OpenQuestion(
            question=question,
            generated_at=time.time(),
            priority=priority,
            source=source,
            context=context
        )
        
        self.open_questions.append(oq)
        self._save_queue()
        
        logger.info(f"📚 ❓ Added open question: {question[:40]}...")
        return oq
    
    def check_if_question_answered(
        self,
        message: str
    ) -> Optional[OpenQuestion]:
        """
        Check if a message answers any open questions.
        Returns the answered question if found.
        """
        message_lower = message.lower()
        
        for q in self.open_questions:
            if q.answered:
                continue
            
            # Check if message relates to question
            q_words = set(q.question.lower().split()[:8])
            m_words = set(message_lower.split())
            
            # Need significant overlap to consider it an answer
            overlap = len(q_words & m_words)
            if overlap >= 3:
                q.answered = True
                q.answer = message[:200]
                q.answered_at = time.time()
                q.satisfaction_on_answer = 0.7  # Base satisfaction
                
                # Trigger satisfaction emotion
                try:
                    from app.core.emotions.emotion_engine import trigger_emotion
                    trigger_emotion("curiosity", "new_information")
                except Exception:
                    pass
                
                self._save_queue()
                logger.info(f"📚 ✅ Question answered: {q.question[:30]}...")
                return q
        
        return None
    
    def update_frustration_levels(self) -> List[OpenQuestion]:
        """
        Update frustration levels for unanswered questions.
        Questions unanswered for too long build frustration.
        
        Returns questions with high frustration.
        """
        now = time.time()
        high_frustration = []
        
        for q in self.open_questions:
            if q.answered:
                continue
            
            hours_waiting = (now - q.generated_at) / 3600
            
            if hours_waiting > self.FRUSTRATION_ONSET_HOURS:
                # Build frustration
                old_frustration = q.frustration_level
                q.frustration_level = min(1.0, (hours_waiting - self.FRUSTRATION_ONSET_HOURS) / 48)
                
                if q.frustration_level > 0.5 and old_frustration <= 0.5:
                    high_frustration.append(q)
        
        if high_frustration:
            self._save_queue()
            # Trigger mild frustration emotion
            try:
                from app.core.emotions.emotion_engine import trigger_emotion
                trigger_emotion("frustration", "unmet_need")
            except Exception:
                pass
        
        return high_frustration
    
    def get_open_questions(self, unanswered_only: bool = True) -> List[str]:
        """Get list of open question strings."""
        if unanswered_only:
            return [q.question for q in self.open_questions if not q.answered]
        return [q.question for q in self.open_questions]
    
    def get_top_open_question(self) -> Optional[OpenQuestion]:
        """Get the highest priority unanswered question."""
        unanswered = [q for q in self.open_questions if not q.answered]
        if not unanswered:
            return None
        return max(unanswered, key=lambda q: q.priority + q.frustration_level * 0.5)
    
    def should_ask_question(self, context: str) -> Optional[str]:
        """
        Determine if Astra should ask an open question in this context.
        Returns question to ask if relevant, None otherwise.
        """
        top_q = self.get_top_open_question()
        if not top_q:
            return None
        
        # Check if context is relevant to the question
        context_lower = context.lower()
        q_words = set(top_q.question.lower().split()[:5])
        c_words = set(context_lower.split())
        
        # If context relates to question, boost desire to ask
        if len(q_words & c_words) >= 2:
            return top_q.question
        
        # High frustration questions get asked regardless
        if top_q.frustration_level > 0.7:
            return top_q.question
        
        return None
    
    def accept_unanswered(self, question: str) -> None:
        """
        Accept that a question won't be answered (acceptance instead of frustration).
        """
        question_lower = question.lower().strip()
        for q in self.open_questions:
            if q.question.lower().strip() == question_lower:
                q.answered = True
                q.answer = "[Accepted as unanswerable]"
                q.answered_at = time.time()
                q.frustration_level = 0  # Release frustration
                self._save_queue()
                logger.info(f"📚 🙏 Accepted unanswered: {question[:30]}...")
                break
    
    def extract_questions_from_thought(self, thought: str) -> List[OpenQuestion]:
        """
        Extract questions from a stream of consciousness thought.
        Called when Astra has thoughts that contain questions.
        """
        questions_added = []
        
        # Split on question marks
        if "?" in thought:
            parts = thought.split("?")
            for part in parts[:-1]:  # All but the last (after final ?)
                # Get the question part
                sentences = part.split(".")
                question = sentences[-1].strip() + "?"
                
                if len(question) > 15 and question.count(" ") >= 2:
                    oq = self.add_open_question(
                        question=question,
                        source="stream_of_consciousness",
                        priority=0.5,
                        context="generated during reflection"
                    )
                    questions_added.append(oq)
        
        return questions_added
    
    def get_curiosity_summary(self) -> Dict[str, Any]:
        """Get a summary of Astra's curiosity state including open questions."""
        base_summary = self.get_learning_summary()
        
        open_qs = [q for q in self.open_questions if not q.answered]
        answered_qs = [q for q in self.open_questions if q.answered]
        frustrated_qs = [q for q in open_qs if q.frustration_level > 0.3]
        
        base_summary.update({
            "open_questions_count": len(open_qs),
            "answered_questions_count": len(answered_qs),
            "frustrated_questions_count": len(frustrated_qs),
            "top_open_question": open_qs[0].question if open_qs else None,
            "curiosity_satisfaction": answered_qs[-1].satisfaction_on_answer if answered_qs else 0.0
        })
        
        return base_summary


# Singleton instance
learning_desire = LearningDesire()
