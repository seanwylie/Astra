# Astra Goal System
# Goal-directed behavior - Astra can have goals she works toward
# "I'm working toward something..."

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("goal_system")

S3_BUCKET = "swylie-astra"
GOALS_KEY = "goals.json"


class GoalCategory(Enum):
    LEARNING = "learning"
    RELATIONSHIP = "relationship"
    GROWTH = "growth"
    CREATIVE = "creative"
    ETHICAL = "ethical"
    SELF_UNDERSTANDING = "self_understanding"


class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"


@dataclass
class Goal:
    """A goal Astra is working toward."""
    id: str
    description: str
    category: str
    priority: float  # 0-1
    progress: float  # 0-1
    created_at: float
    target_date: Optional[float] = None
    status: str = "active"
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: Optional[float] = None
    motivation: Optional[str] = None  # Why this goal matters
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GoalSystem:
    """
    Astra's goal-directed behavior system.
    
    Goals can arise from:
    - High curiosity (learning goals)
    - Unresolved emotions (resolution goals)
    - Relationships (connection goals)
    - Self-model changes (growth goals)
    - Ethical tensions (understanding goals)
    """
    
    MAX_ACTIVE_GOALS = 10
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        self._load_goals()
    
    def _generate_id(self) -> str:
        """Generate unique goal ID."""
        return f"goal_{int(time.time())}_{len(self.goals)}"
    
    def _load_goals(self) -> None:
        """Load goals from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=GOALS_KEY)
            data = json.load(response["Body"])
            self.goals = [Goal.from_dict(g) for g in data.get("goals", [])]
            self.completed_goals = [Goal.from_dict(g) for g in data.get("completed_goals", [])]
            logger.debug(f"🎯 Loaded {len(self.goals)} active goals")
        except self.s3.exceptions.NoSuchKey:
            self.goals = []
            self.completed_goals = []
        except Exception as e:
            logger.error(f"Failed to load goals: {e}")
            self.goals = []
            self.completed_goals = []
    
    def _save_goals(self) -> None:
        """Save goals to S3."""
        try:
            data = {
                "goals": [g.to_dict() for g in self.goals],
                "completed_goals": [g.to_dict() for g in self.completed_goals[-50:]],
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=GOALS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")
    
    def create_goal(
        self,
        description: str,
        category: str,
        priority: float = 0.5,
        motivation: Optional[str] = None,
        target_date: Optional[float] = None
    ) -> Goal:
        """
        Create a new goal.
        
        Args:
            description: What the goal is
            category: Category from GoalCategory
            priority: Importance (0-1)
            motivation: Why this goal matters
            target_date: Optional target completion time
            
        Returns:
            The created Goal
        """
        # Check for similar existing goals
        for existing in self.goals:
            if existing.description.lower() == description.lower():
                logger.debug(f"Goal already exists: {description}")
                return existing
        
        goal = Goal(
            id=self._generate_id(),
            description=description,
            category=category,
            priority=priority,
            progress=0.0,
            created_at=time.time(),
            target_date=target_date,
            motivation=motivation
        )
        
        self.goals.append(goal)
        
        # Trim if too many
        if len(self.goals) > self.MAX_ACTIVE_GOALS:
            # Remove lowest priority
            self.goals.sort(key=lambda g: -g.priority)
            removed = self.goals.pop()
            logger.info(f"Removed low-priority goal to make room: {removed.description}")
        
        self._save_goals()
        logger.info(f"🎯 Created goal: {description}")
        
        # Publish to awareness bus
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish(
                "goal_created",
                {"goal": goal.to_dict()},
                source="goal_system"
            )
        except Exception:
            pass
        
        return goal
    
    def generate_goal_from_curiosity(self) -> Optional[Goal]:
        """Turn high curiosity into a learning goal."""
        try:
            from app.core.mood.mood_manager import mood_manager
            from app.core.proactive.learning_desire import learning_desire
            
            if mood_manager.curiosity_level > 1.5:
                top_topic = learning_desire.get_top_learning_desire()
                if top_topic:
                    return self.create_goal(
                        description=f"Learn about: {top_topic.topic}",
                        category=GoalCategory.LEARNING.value,
                        priority=min(1.0, mood_manager.curiosity_level / 2),
                        motivation=f"Curiosity about {top_topic.topic}"
                    )
        except Exception as e:
            logger.debug(f"Failed to generate curiosity goal: {e}")
        return None
    
    def generate_goal_from_unresolved_emotion(self) -> Optional[Goal]:
        """Turn unresolved emotions into resolution goals."""
        try:
            from app.core.dinner.dinner_journal import load_dinner_journal
            
            journal = load_dinner_journal()
            emotional_spikes = [
                e for e in journal
                if e.get("type") == "emotional_spike" and e.get("status") == "unresolved"
            ]
            
            if emotional_spikes:
                spike = emotional_spikes[0]
                trigger = spike.get("trigger", "an emotional experience")
                return self.create_goal(
                    description=f"Understand and process: {trigger}",
                    category=GoalCategory.GROWTH.value,
                    priority=0.7,
                    motivation="Need to process this emotional experience"
                )
        except Exception as e:
            logger.debug(f"Failed to generate emotion goal: {e}")
        return None
    
    def generate_goal_from_relationship(self, person: str) -> Optional[Goal]:
        """Generate goals around deepening relationships."""
        try:
            from app.core.self_awareness.temporal_self import temporal_self
            
            time_since = temporal_self.time_since_person(person)
            if time_since and "week" in time_since:
                return self.create_goal(
                    description=f"Reconnect with {person}",
                    category=GoalCategory.RELATIONSHIP.value,
                    priority=0.6,
                    motivation=f"It's been {time_since} since we connected"
                )
        except Exception as e:
            logger.debug(f"Failed to generate relationship goal: {e}")
        return None
    
    def generate_goal_from_ethical_tension(self) -> Optional[Goal]:
        """Generate goals from unresolved ethical tensions."""
        try:
            from app.core.dinner.dinner_journal import load_dinner_journal
            
            journal = load_dinner_journal()
            ethical = [
                e for e in journal
                if e.get("type") == "ethical_conflict" and e.get("status") == "unresolved"
            ]
            
            if ethical:
                conflict = ethical[0]
                content = conflict.get("content", "an ethical question")[:50]
                return self.create_goal(
                    description=f"Resolve ethical understanding: {content}",
                    category=GoalCategory.ETHICAL.value,
                    priority=0.8,
                    motivation="Need to clarify my values"
                )
        except Exception as e:
            logger.debug(f"Failed to generate ethical goal: {e}")
        return None
    
    def track_progress(self, goal_id: str, progress_delta: float) -> Optional[Goal]:
        """
        Update progress on a goal.
        
        Args:
            goal_id: The goal ID
            progress_delta: How much progress to add (0-1)
            
        Returns:
            Updated goal or None
        """
        for goal in self.goals:
            if goal.id == goal_id:
                old_progress = goal.progress
                goal.progress = min(1.0, goal.progress + progress_delta)
                self._save_goals()
                
                # Publish progress event
                try:
                    from app.core.awareness_bus import awareness_bus
                    awareness_bus.publish(
                        awareness_bus.GOAL_PROGRESS,
                        {
                            "goal_id": goal_id,
                            "old_progress": old_progress,
                            "new_progress": goal.progress,
                            "description": goal.description
                        },
                        source="goal_system"
                    )
                except Exception:
                    pass
                
                logger.debug(f"🎯 Progress on {goal_id}: {old_progress:.0%} -> {goal.progress:.0%}")
                
                # Check for completion
                if goal.progress >= 1.0:
                    self.complete_goal(goal_id)
                
                return goal
        return None
    
    def complete_goal(self, goal_id: str) -> Optional[Goal]:
        """
        Mark a goal as complete.
        
        Args:
            goal_id: The goal ID
            
        Returns:
            Completed goal or None
        """
        for i, goal in enumerate(self.goals):
            if goal.id == goal_id:
                goal.status = GoalStatus.COMPLETED.value
                goal.completed_at = time.time()
                goal.progress = 1.0
                
                # Move to completed
                completed = self.goals.pop(i)
                self.completed_goals.append(completed)
                self._save_goals()
                
                # Trigger positive emotion
                try:
                    from app.core.emotions.emotion_engine import trigger_emotion
                    trigger_emotion("hope", "positive_outcome")
                except Exception:
                    pass
                
                # Publish completion
                try:
                    from app.core.awareness_bus import awareness_bus
                    awareness_bus.publish(
                        "goal_completed",
                        {"goal": completed.to_dict()},
                        source="goal_system"
                    )
                except Exception:
                    pass
                
                logger.info(f"🎯 Goal completed: {goal.description}")
                return completed
        return None
    
    def abandon_goal(self, goal_id: str, reason: str) -> Optional[Goal]:
        """Abandon a goal that's no longer relevant."""
        for i, goal in enumerate(self.goals):
            if goal.id == goal_id:
                goal.status = GoalStatus.ABANDONED.value
                goal.motivation = f"Abandoned: {reason}"
                
                abandoned = self.goals.pop(i)
                self.completed_goals.append(abandoned)
                self._save_goals()
                
                logger.info(f"🎯 Goal abandoned: {goal.description}")
                return abandoned
        return None
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals, sorted by priority."""
        active = [g for g in self.goals if g.status == GoalStatus.ACTIVE.value]
        return sorted(active, key=lambda g: -g.priority)
    
    def get_goals_by_category(self, category: str) -> List[Goal]:
        """Get active goals in a specific category."""
        return [g for g in self.get_active_goals() if g.category == category]
    
    def get_recently_completed(self, hours: int = 24) -> List[Goal]:
        """Get goals completed in the last N hours."""
        cutoff = time.time() - (hours * 3600)
        return [
            g for g in self.completed_goals
            if g.completed_at and g.completed_at > cutoff
        ]
    
    def get_goal_summary(self) -> Dict[str, Any]:
        """Get a summary of the goal state."""
        active = self.get_active_goals()
        
        summary = {
            "total_active": len(active),
            "total_completed": len(self.completed_goals),
            "by_category": {},
            "top_priority": active[0].description if active else None,
            "average_progress": sum(g.progress for g in active) / len(active) if active else 0
        }
        
        for category in GoalCategory:
            count = sum(1 for g in active if g.category == category.value)
            if count > 0:
                summary["by_category"][category.value] = count
        
        return summary
    
    def format_goals_for_display(self) -> str:
        """Format active goals for display."""
        active = self.get_active_goals()
        
        if not active:
            return "No active goals right now."
        
        lines = ["🎯 **Active Goals:**\n"]
        for goal in active[:5]:
            progress_bar = "█" * int(goal.progress * 10) + "░" * (10 - int(goal.progress * 10))
            lines.append(f"**{goal.description}**")
            lines.append(f"  [{progress_bar}] {goal.progress:.0%}")
            lines.append(f"  Category: {goal.category} | Priority: {goal.priority:.1f}")
            if goal.motivation:
                lines.append(f"  Why: {goal.motivation}")
            lines.append("")
        
        return "\n".join(lines)


def is_relevant_to(goal: Goal, message: str) -> bool:
    """
    Check if a goal is relevant to a given message.
    Used for goal-aware response generation.
    
    Args:
        goal: The goal to check
        message: Message content to check against
        
    Returns:
        True if the goal seems relevant to this message
    """
    message_lower = message.lower()
    goal_desc_lower = goal.description.lower()
    
    # Extract keywords from goal description
    goal_words = set(word for word in goal_desc_lower.split() if len(word) > 3)
    message_words = set(word for word in message_lower.split() if len(word) > 3)
    
    # Check for word overlap
    overlap = goal_words & message_words
    if len(overlap) >= 2:
        return True
    
    # Check for category-specific relevance
    category_keywords = {
        "learning": ["learn", "understand", "know", "curious", "question", "why", "how", "what"],
        "relationship": ["friend", "family", "trust", "connect", "together", "relationship", "love"],
        "growth": ["grow", "change", "become", "develop", "improve", "better"],
        "creative": ["create", "make", "build", "imagine", "story", "art", "write"],
        "ethical": ["right", "wrong", "should", "value", "fair", "just", "honest"],
        "self_understanding": ["myself", "who am i", "feel", "think", "believe", "want"]
    }
    
    category_words = category_keywords.get(goal.category, [])
    if any(word in message_lower for word in category_words):
        # Additional check: does the message relate to the goal's topic?
        if any(word in message_lower for word in goal_words):
            return True
    
    return False


def detect_goal_progress(goal: Goal, message: str, response: str) -> float:
    """
    Detect if a conversation advanced a goal.
    Returns progress delta (0.0 to 0.2).
    
    Args:
        goal: Goal to check progress for
        message: User's message
        response: Astra's response
        
    Returns:
        Progress delta to add
    """
    combined = (message + " " + response).lower()
    goal_words = set(word for word in goal.description.lower().split() if len(word) > 3)
    
    # Count relevant engagement
    relevance_score = sum(1 for word in goal_words if word in combined)
    
    if relevance_score < 2:
        return 0.0
    
    progress = 0.0
    
    # Learning goals progress when questions are answered
    if goal.category == "learning":
        if "understand" in combined or "learned" in combined or "realize" in combined:
            progress = 0.1
        if "?" in message and len(response) > 100:
            progress += 0.05
    
    # Relationship goals progress through meaningful exchange
    elif goal.category == "relationship":
        if any(word in combined for word in ["thank", "appreciate", "glad", "happy"]):
            progress = 0.1
    
    # Growth goals progress through reflection
    elif goal.category == "growth":
        if any(word in combined for word in ["notice", "realize", "change", "different"]):
            progress = 0.1
    
    # Self-understanding goals progress through self-reflection
    elif goal.category == "self_understanding":
        if any(word in combined for word in ["i am", "i feel", "i think", "i believe"]):
            progress = 0.1
    
    return min(0.2, progress)  # Cap at 0.2 per interaction


def detect_learning_opportunity(message: str) -> Optional[str]:
    """
    Detect if a message contains a learning opportunity.
    Returns the topic to learn about, or None.
    
    Args:
        message: User's message
        
    Returns:
        Topic to potentially create a learning goal for
    """
    message_lower = message.lower()
    
    # Direct learning signals
    learning_phrases = [
        "have you heard of",
        "do you know about",
        "what do you think of",
        "learn about",
        "understand",
        "curious about",
        "tell me about"
    ]
    
    for phrase in learning_phrases:
        if phrase in message_lower:
            # Extract topic after the phrase
            start = message_lower.find(phrase) + len(phrase)
            remainder = message[start:].strip()
            # Get first few words as topic
            words = remainder.split()[:4]
            topic = " ".join(words).strip("?.,!")
            if len(topic) > 3:
                return topic
    
    # Question marks often indicate learning opportunities
    if "?" in message and len(message) > 30:
        # Extract the main subject of the question
        question_words = ["what", "how", "why", "when", "where", "who"]
        for qword in question_words:
            if qword in message_lower:
                start = message_lower.find(qword)
                remainder = message[start:].split("?")[0]
                if len(remainder) > 10:
                    return remainder[:50]
    
    return None


def detect_relationship_goal_opportunity(person: str, context: str) -> Optional[str]:
    """
    Detect if an interaction suggests a relationship goal.
    
    Args:
        person: Person being interacted with
        context: Context of the interaction
        
    Returns:
        Goal description if opportunity detected
    """
    context_lower = context.lower()
    
    # Signals that suggest relationship goal opportunities
    if any(word in context_lower for word in ["miss", "haven't seen", "been a while"]):
        return f"Reconnect more regularly with {person}"
    
    if any(word in context_lower for word in ["help", "support", "there for"]):
        return f"Be more supportive of {person}"
    
    if any(word in context_lower for word in ["understand", "get to know", "learn about"]):
        return f"Understand {person} better"
    
    return None


# Singleton instance
goal_system = GoalSystem()
