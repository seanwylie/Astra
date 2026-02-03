# Astra Working Memory System
# Maintains reasoning state across turns within a conversation
# Capacity-limited like human working memory (7±2 items)

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from app.logging_config import get_logger

logger = get_logger("working_memory")

S3_BUCKET = "swylie-astra"
WORKING_MEMORY_KEY = "working_memory.json"

s3 = boto3.client("s3")


@dataclass
class Hypothesis:
    """A hypothesis Astra is currently considering."""
    id: str
    content: str
    confidence: float  # 0-1
    created_at: float
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    source: str = "inference"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Hypothesis":
        return cls(**data)


@dataclass
class PendingQuestion:
    """A question Astra wants answered."""
    question: str
    priority: float  # 0-1
    asked_at: float
    context: str
    answered: bool = False
    answer: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PendingQuestion":
        return cls(**data)


class WorkingMemory:
    """
    Astra's Working Memory - maintains reasoning state across conversation turns.
    
    Inspired by cognitive psychology's working memory model:
    - Limited capacity (7±2 items)
    - Oldest items displaced when capacity exceeded
    - Integrates perception, memory, and reasoning
    - Enables coherent multi-turn reasoning
    
    Components:
    - Active hypotheses: Current theories being considered
    - Pending questions: Questions Astra wants answered
    - Reasoning context: Variables and facts being tracked
    - Goal stack: What Astra is trying to accomplish
    """
    
    # Capacity limits (based on Miller's 7±2)
    MAX_HYPOTHESES = 5
    MAX_QUESTIONS = 5
    MAX_CONTEXT_ITEMS = 7
    MAX_GOALS = 3
    
    # Working memory decay (items older than this may be displaced)
    DECAY_MINUTES = 30
    
    def __init__(self):
        self.hypotheses: List[Hypothesis] = []
        self.pending_questions: List[PendingQuestion] = []
        self.reasoning_context: Dict[str, Any] = {}
        self.goal_stack: List[str] = []
        self.last_conversation_id: Optional[str] = None
        self.last_updated: float = 0
        self._load_state()
        logger.debug("🧠 Working Memory initialized - maintaining reasoning state")
    
    def _load_state(self) -> None:
        """Load working memory state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=WORKING_MEMORY_KEY)
            data = json.load(response["Body"])
            
            self.hypotheses = [
                Hypothesis.from_dict(h) for h in data.get("hypotheses", [])
            ]
            self.pending_questions = [
                PendingQuestion.from_dict(q) for q in data.get("pending_questions", [])
            ]
            self.reasoning_context = data.get("reasoning_context", {})
            self.goal_stack = data.get("goal_stack", [])
            self.last_conversation_id = data.get("last_conversation_id")
            self.last_updated = data.get("last_updated", 0)
            
            # Apply decay
            self._apply_decay()
            
            logger.debug(f"🧠 Loaded working memory: {len(self.hypotheses)} hypotheses, {len(self.pending_questions)} questions")
        except s3.exceptions.NoSuchKey:
            logger.debug("🧠 No working memory found. Starting fresh.")
        except Exception as e:
            logger.warning(f"🧠 Error loading working memory: {e}")
    
    def _save_state(self) -> None:
        """Save working memory state to S3."""
        try:
            self.last_updated = time.time()
            data = {
                "hypotheses": [h.to_dict() for h in self.hypotheses],
                "pending_questions": [q.to_dict() for q in self.pending_questions],
                "reasoning_context": self.reasoning_context,
                "goal_stack": self.goal_stack,
                "last_conversation_id": self.last_conversation_id,
                "last_updated": self.last_updated
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=WORKING_MEMORY_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🧠 Error saving working memory: {e}")
    
    def _apply_decay(self) -> None:
        """Apply time-based decay to working memory items."""
        now = time.time()
        cutoff = now - (self.DECAY_MINUTES * 60)
        
        # Remove old hypotheses with low confidence
        self.hypotheses = [
            h for h in self.hypotheses
            if h.created_at > cutoff or h.confidence > 0.7
        ]
        
        # Remove old unanswered questions
        self.pending_questions = [
            q for q in self.pending_questions
            if q.asked_at > cutoff or q.priority > 0.7 or q.answered
        ]
    
    def _generate_id(self) -> str:
        return f"hyp_{int(time.time() * 1000) % 1000000}"
    
    # ========== Hypothesis Management ==========
    
    def add_hypothesis(
        self,
        content: str,
        confidence: float = 0.5,
        source: str = "inference"
    ) -> Hypothesis:
        """Add a hypothesis to working memory."""
        # Check if similar hypothesis exists
        for h in self.hypotheses:
            if self._similar_content(h.content, content):
                # Boost existing hypothesis
                h.confidence = min(1.0, h.confidence + 0.1)
                self._save_state()
                return h
        
        hypothesis = Hypothesis(
            id=self._generate_id(),
            content=content,
            confidence=confidence,
            created_at=time.time(),
            source=source
        )
        
        self.hypotheses.append(hypothesis)
        
        # Enforce capacity limit
        if len(self.hypotheses) > self.MAX_HYPOTHESES:
            # Remove lowest confidence hypothesis
            self.hypotheses.sort(key=lambda h: h.confidence, reverse=True)
            removed = self.hypotheses.pop()
            logger.debug(f"🧠 Displaced hypothesis: {removed.content[:30]}...")
        
        self._save_state()
        logger.info(f"🧠 Added hypothesis: {content[:40]}...")
        return hypothesis
    
    def update_hypothesis(
        self,
        hypothesis_id: str,
        evidence: str,
        supports: bool
    ) -> bool:
        """Update a hypothesis with new evidence."""
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                if supports:
                    h.evidence_for.append(evidence)
                    h.confidence = min(1.0, h.confidence + 0.1)
                else:
                    h.evidence_against.append(evidence)
                    h.confidence = max(0.0, h.confidence - 0.15)
                
                # Remove if confidence too low
                if h.confidence < 0.2:
                    self.hypotheses.remove(h)
                    logger.info(f"🧠 Abandoned hypothesis: {h.content[:30]}...")
                
                self._save_state()
                return True
        return False
    
    def get_active_hypotheses(self) -> List[str]:
        """Get list of active hypothesis contents."""
        return [h.content for h in sorted(self.hypotheses, key=lambda h: -h.confidence)]
    
    # ========== Question Management ==========
    
    def add_question(
        self,
        question: str,
        priority: float = 0.5,
        context: str = ""
    ) -> PendingQuestion:
        """Add a question Astra wants answered."""
        # Check for duplicate
        for q in self.pending_questions:
            if self._similar_content(q.question, question):
                q.priority = min(1.0, q.priority + 0.1)
                self._save_state()
                return q
        
        pq = PendingQuestion(
            question=question,
            priority=priority,
            asked_at=time.time(),
            context=context
        )
        
        self.pending_questions.append(pq)
        
        # Enforce capacity
        if len(self.pending_questions) > self.MAX_QUESTIONS:
            self.pending_questions.sort(key=lambda q: q.priority, reverse=True)
            self.pending_questions.pop()
        
        self._save_state()
        logger.info(f"🧠 Added question: {question[:40]}...")
        return pq
    
    def answer_question(self, question: str, answer: str) -> bool:
        """Mark a question as answered."""
        for q in self.pending_questions:
            if self._similar_content(q.question, question):
                q.answered = True
                q.answer = answer
                self._save_state()
                logger.info(f"🧠 Question answered: {question[:30]}...")
                return True
        return False
    
    def get_pending_questions(self) -> List[str]:
        """Get unanswered questions."""
        return [
            q.question for q in self.pending_questions
            if not q.answered
        ]
    
    # ========== Context Management ==========
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a reasoning context variable."""
        self.reasoning_context[key] = value
        
        # Enforce capacity
        if len(self.reasoning_context) > self.MAX_CONTEXT_ITEMS:
            # Remove oldest (first) item
            oldest_key = next(iter(self.reasoning_context))
            del self.reasoning_context[oldest_key]
        
        self._save_state()
    
    def get_context(self, key: str) -> Any:
        """Get a reasoning context variable."""
        return self.reasoning_context.get(key)
    
    def clear_context(self) -> None:
        """Clear all context."""
        self.reasoning_context.clear()
        self._save_state()
    
    # ========== Goal Management ==========
    
    def push_goal(self, goal: str) -> None:
        """Push a goal onto the goal stack."""
        if goal not in self.goal_stack:
            self.goal_stack.append(goal)
            if len(self.goal_stack) > self.MAX_GOALS:
                self.goal_stack.pop(0)  # Remove oldest goal
            self._save_state()
    
    def pop_goal(self) -> Optional[str]:
        """Pop and return the most recent goal."""
        if self.goal_stack:
            goal = self.goal_stack.pop()
            self._save_state()
            return goal
        return None
    
    def current_goal(self) -> Optional[str]:
        """Get the current (most recent) goal."""
        return self.goal_stack[-1] if self.goal_stack else None
    
    # ========== Integration Methods ==========
    
    def process_message(self, user_message: str, astra_response: str) -> None:
        """
        Process a conversation exchange to update working memory.
        Called after each message exchange.
        """
        # Extract potential hypotheses from response
        if "I think" in astra_response or "I wonder if" in astra_response or "perhaps" in astra_response.lower():
            # Extract the hypothesis part
            for marker in ["I think ", "I wonder if ", "perhaps "]:
                if marker.lower() in astra_response.lower():
                    idx = astra_response.lower().find(marker.lower())
                    hypothesis_text = astra_response[idx + len(marker):].split(".")[0]
                    if len(hypothesis_text) > 10:
                        self.add_hypothesis(hypothesis_text[:100], confidence=0.5, source="self_statement")
                        break
        
        # Extract questions Astra asked
        if "?" in astra_response:
            sentences = astra_response.split("?")
            for s in sentences[:-1]:  # All but last (which follows the ?)
                question = s.split(".")[-1].strip() + "?"
                if len(question) > 10 and question.count(" ") >= 2:
                    self.add_question(question, priority=0.5, context=user_message[:50])
        
        # Check if user answered any pending questions
        for q in self.pending_questions:
            if not q.answered:
                # Simple check if user message relates to question
                q_words = set(q.question.lower().split()[:5])
                u_words = set(user_message.lower().split())
                if len(q_words & u_words) >= 2:
                    self.answer_question(q.question, user_message[:100])
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of working memory for prompt inclusion."""
        active_hyps = self.get_active_hypotheses()
        pending_qs = self.get_pending_questions()
        
        return {
            "has_content": bool(active_hyps or pending_qs or self.goal_stack),
            "active_hypotheses": active_hyps[:2],
            "pending_questions": pending_qs[:2],
            "current_goal": self.current_goal(),
            "context_keys": list(self.reasoning_context.keys())[:3]
        }
    
    def new_conversation(self, conversation_id: str) -> None:
        """Signal start of a new conversation - may clear some state."""
        if conversation_id != self.last_conversation_id:
            # Clear ephemeral context but keep persistent hypotheses and questions
            self.reasoning_context.clear()
            self.goal_stack.clear()
            self.last_conversation_id = conversation_id
            self._save_state()
    
    def _similar_content(self, a: str, b: str) -> bool:
        """Check if two content strings are similar."""
        a_words = set(a.lower().split()[:8])
        b_words = set(b.lower().split()[:8])
        if not a_words or not b_words:
            return False
        overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
        return overlap > 0.5
    
    def describe_state(self) -> str:
        """Describe current working memory state."""
        parts = []
        
        if self.hypotheses:
            parts.append(f"I'm considering {len(self.hypotheses)} hypothesis(es): {self.hypotheses[0].content[:40]}...")
        
        if self.pending_questions:
            unanswered = [q for q in self.pending_questions if not q.answered]
            if unanswered:
                parts.append(f"I have {len(unanswered)} question(s) I'd like answered: {unanswered[0].question[:40]}...")
        
        if self.goal_stack:
            parts.append(f"My current goal: {self.goal_stack[-1]}")
        
        if not parts:
            return "My working memory is clear—ready for new reasoning."
        
        return " ".join(parts)


# Singleton instance
working_memory = WorkingMemory()
