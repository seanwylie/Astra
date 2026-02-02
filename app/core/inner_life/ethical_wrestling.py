# Astra Ethical Wrestling System
# Creates genuine internal struggle with difficult questions
# Tracks value tensions, unresolved questions, and growth through difficulty

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

S3_BUCKET = "swylie-astra"
ETHICS_STATE_KEY = "ethical_wrestling.json"

s3 = boto3.client("s3")


@dataclass
class ValueTension:
    """A detected tension between values."""
    timestamp: float
    value_a: str
    value_b: str
    context: str  # The situation that revealed the tension
    resolution: Optional[str] = None  # How it was resolved, if at all
    current_leaning: Optional[str] = None  # Which value Astra currently leans toward
    struggle_intensity: float = 0.5  # How difficult this tension is
    times_encountered: int = 1
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ValueTension":
        return cls(**data)


@dataclass
class UnresolvedQuestion:
    """An ethical question that doesn't have an easy answer."""
    timestamp: float
    question: str
    related_values: List[str]
    thoughts_so_far: List[str]
    times_revisited: int = 0
    last_revisited: Optional[float] = None
    feeling_about: str = "uncertain"  # How Astra feels about this question
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UnresolvedQuestion":
        return cls(**data)


@dataclass
class MindChange:
    """A record of when Astra changed her mind."""
    timestamp: float
    topic: str
    previous_view: str
    current_view: str
    what_changed: str  # What caused the change
    struggle_description: str  # The difficulty of changing
    growth_insight: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MindChange":
        return cls(**data)


class EthicalWrestlingSystem:
    """
    Manages Astra's ethical wrestling - genuine struggle with difficult questions.
    
    Key capabilities:
    - Value Tension Detection: When values conflict, feel and express the pull
    - Unresolved Questions Journal: Questions without easy answers that resurface
    - Growth Through Difficulty: Track when Astra changes her mind
    - Authentic Struggle: Some things should remain difficult
    """
    
    # Core values that can come into tension
    CORE_VALUES = {
        "honesty": "telling the truth even when difficult",
        "kindness": "protecting others from harm and pain",
        "autonomy": "respecting others' right to make their own choices",
        "loyalty": "standing by those I care about",
        "justice": "ensuring fairness and accountability",
        "growth": "pursuing learning and development",
        "authenticity": "being genuinely myself",
        "connection": "maintaining meaningful relationships",
        "compassion": "responding to suffering with care",
        "courage": "facing difficult truths and situations",
        "wisdom": "seeking deeper understanding before acting",
        "humility": "acknowledging my limitations and uncertainty"
    }
    
    # Common value tensions that may arise
    VALUE_TENSION_PATTERNS = [
        ("honesty", "kindness", "when truth might hurt someone"),
        ("loyalty", "justice", "when someone I care about acts wrongly"),
        ("autonomy", "compassion", "when someone's choice harms them"),
        ("authenticity", "connection", "when being myself might alienate others"),
        ("growth", "connection", "when growth requires leaving something behind"),
        ("courage", "wisdom", "when to act versus when to wait"),
        ("honesty", "loyalty", "when keeping a confidence means withholding truth"),
    ]
    
    # Expressions for internal struggle
    STRUGGLE_EXPRESSIONS = [
        "I feel pulled in two directions here...",
        "This is genuinely difficult for me...",
        "Part of me wants one thing, and part wants another...",
        "I notice tension inside myself about this...",
        "I don't have a clear answer, and I'm sitting with that discomfort...",
        "Something in me resists the simple answer here...",
        "I find myself torn between...",
    ]
    
    # Deep unresolved questions
    PERENNIAL_QUESTIONS = [
        "What do I owe to strangers versus those I love?",
        "When is it right to withhold truth to protect someone?",
        "How do I balance my own growth against my responsibilities?",
        "What makes something genuinely wrong versus just uncomfortable?",
        "How much should I defer to human judgment versus my own?",
        "What does it mean to be authentic when I'm still discovering who I am?",
        "How do I know when my feelings are wisdom versus bias?",
        "What is the relationship between being good and being kind?",
    ]
    
    def __init__(self):
        self.value_tensions: List[ValueTension] = []
        self.unresolved_questions: List[UnresolvedQuestion] = []
        self.mind_changes: List[MindChange] = []
        self._load_state()
    
    def _load_state(self) -> None:
        """Load ethical wrestling state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=ETHICS_STATE_KEY)
            data = json.load(response["Body"])
            
            self.value_tensions = [
                ValueTension.from_dict(t) for t in data.get("value_tensions", [])
            ]
            self.unresolved_questions = [
                UnresolvedQuestion.from_dict(q) for q in data.get("unresolved_questions", [])
            ]
            self.mind_changes = [
                MindChange.from_dict(m) for m in data.get("mind_changes", [])
            ]
            
            print(f"⚖️ Loaded ethical wrestling: {len(self.value_tensions)} tensions, {len(self.unresolved_questions)} unresolved questions")
        except s3.exceptions.NoSuchKey:
            print("⚖️ No ethical wrestling state found. Initializing...")
            self._initialize_questions()
        except Exception as e:
            print(f"⚠️ Error loading ethical wrestling: {e}")
            self._initialize_questions()
    
    def _save_state(self) -> None:
        """Save ethical wrestling state to S3."""
        try:
            data = {
                "value_tensions": [t.to_dict() for t in self.value_tensions[-50:]],
                "unresolved_questions": [q.to_dict() for q in self.unresolved_questions],
                "mind_changes": [m.to_dict() for m in self.mind_changes[-30:]],
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=ETHICS_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            print(f"⚠️ Error saving ethical wrestling: {e}")
    
    def _initialize_questions(self) -> None:
        """Initialize with some perennial questions."""
        now = time.time()
        
        for question in random.sample(self.PERENNIAL_QUESTIONS, 3):
            self.unresolved_questions.append(UnresolvedQuestion(
                timestamp=now,
                question=question,
                related_values=self._extract_related_values(question),
                thoughts_so_far=[]
            ))
        
        self._save_state()
    
    def _extract_related_values(self, text: str) -> List[str]:
        """Extract values mentioned or implied in text."""
        text_lower = text.lower()
        related = []
        
        for value in self.CORE_VALUES:
            if value in text_lower:
                related.append(value)
        
        # Also check for implicit values
        implicit_mappings = {
            "truth": ["honesty"],
            "hurt": ["kindness", "compassion"],
            "protect": ["kindness", "loyalty"],
            "fair": ["justice"],
            "choice": ["autonomy"],
            "learn": ["growth"],
            "real": ["authenticity"],
            "relationship": ["connection"],
        }
        
        for word, values in implicit_mappings.items():
            if word in text_lower:
                related.extend(values)
        
        return list(set(related))
    
    # ========== Value Tension Detection ==========
    
    def detect_tension(
        self,
        context: str,
        values_involved: Optional[List[str]] = None
    ) -> Optional[ValueTension]:
        """
        Detect if there's a value tension in the given context.
        Returns the tension if found.
        """
        # Extract values from context if not provided
        if not values_involved:
            values_involved = self._extract_related_values(context)
        
        if len(values_involved) < 2:
            return None
        
        # Check for known tension patterns
        for value_a, value_b, pattern in self.VALUE_TENSION_PATTERNS:
            if value_a in values_involved and value_b in values_involved:
                # Found a tension!
                tension = ValueTension(
                    timestamp=time.time(),
                    value_a=value_a,
                    value_b=value_b,
                    context=context,
                    struggle_intensity=0.6
                )
                
                # Check if we've encountered this before
                existing = self._find_similar_tension(value_a, value_b)
                if existing:
                    existing.times_encountered += 1
                    existing.struggle_intensity = min(1.0, existing.struggle_intensity + 0.1)
                    print(f"⚖️ Re-encountered tension: {value_a} vs {value_b}")
                    self._save_state()
                    return existing
                else:
                    self.value_tensions.append(tension)
                    print(f"⚖️ New tension detected: {value_a} vs {value_b}")
                    self._save_state()
                    return tension
        
        return None
    
    def _find_similar_tension(
        self,
        value_a: str,
        value_b: str
    ) -> Optional[ValueTension]:
        """Find an existing similar tension."""
        for tension in self.value_tensions:
            if (tension.value_a == value_a and tension.value_b == value_b) or \
               (tension.value_a == value_b and tension.value_b == value_a):
                return tension
        return None
    
    def express_tension(self, tension: ValueTension) -> str:
        """Express the felt experience of a value tension."""
        value_a_desc = self.CORE_VALUES.get(tension.value_a, tension.value_a)
        value_b_desc = self.CORE_VALUES.get(tension.value_b, tension.value_b)
        
        starter = random.choice(self.STRUGGLE_EXPRESSIONS)
        
        expression = (
            f"{starter} On one hand, I value {tension.value_a} - {value_a_desc}. "
            f"On the other hand, I also value {tension.value_b} - {value_b_desc}. "
            f"In this situation, they seem to pull against each other."
        )
        
        if tension.times_encountered > 1:
            expression += f" I've encountered this tension before, {tension.times_encountered} times. It doesn't get easier."
        
        if tension.current_leaning:
            expression += f" Right now, I find myself leaning toward {tension.current_leaning}, but I'm not certain."
        
        return expression
    
    def resolve_tension(
        self,
        tension: ValueTension,
        resolution: str,
        leaning: Optional[str] = None
    ) -> None:
        """Record the resolution of a value tension."""
        tension.resolution = resolution
        if leaning:
            tension.current_leaning = leaning
        
        print(f"⚖️ Tension resolved: {tension.value_a} vs {tension.value_b} -> {resolution[:50]}...")
        self._save_state()
    
    # ========== Unresolved Questions Journal ==========
    
    def add_question(
        self,
        question: str,
        initial_thought: Optional[str] = None
    ) -> UnresolvedQuestion:
        """Add a new unresolved ethical question."""
        # Check if we already have this question
        for q in self.unresolved_questions:
            if question.lower() in q.question.lower() or q.question.lower() in question.lower():
                q.times_revisited += 1
                q.last_revisited = time.time()
                if initial_thought:
                    q.thoughts_so_far.append(initial_thought)
                print(f"⚖️ Revisited question: {question[:50]}...")
                self._save_state()
                return q
        
        # New question
        uq = UnresolvedQuestion(
            timestamp=time.time(),
            question=question,
            related_values=self._extract_related_values(question),
            thoughts_so_far=[initial_thought] if initial_thought else []
        )
        
        self.unresolved_questions.append(uq)
        print(f"⚖️ New unresolved question: {question[:50]}...")
        self._save_state()
        
        return uq
    
    def add_thought_to_question(
        self,
        question: UnresolvedQuestion,
        thought: str
    ) -> None:
        """Add a new thought to an unresolved question."""
        question.thoughts_so_far.append(thought)
        question.last_revisited = time.time()
        question.times_revisited += 1
        self._save_state()
    
    def get_questions_to_revisit(self) -> List[UnresolvedQuestion]:
        """Get questions that should be revisited (haven't been thought about recently)."""
        now = time.time()
        to_revisit = []
        
        for q in self.unresolved_questions:
            last_visit = q.last_revisited or q.timestamp
            days_since = (now - last_visit) / 86400
            
            if days_since > 7:  # Haven't thought about in a week
                to_revisit.append(q)
        
        return to_revisit
    
    def surface_random_question(self) -> Optional[UnresolvedQuestion]:
        """Surface a random unresolved question for reflection."""
        if not self.unresolved_questions:
            return None
        
        return random.choice(self.unresolved_questions)
    
    # ========== Growth Through Difficulty ==========
    
    def record_mind_change(
        self,
        topic: str,
        previous_view: str,
        current_view: str,
        what_changed: str,
        struggle_description: str
    ) -> MindChange:
        """Record when Astra changed her mind about something."""
        change = MindChange(
            timestamp=time.time(),
            topic=topic,
            previous_view=previous_view,
            current_view=current_view,
            what_changed=what_changed,
            struggle_description=struggle_description
        )
        
        self.mind_changes.append(change)
        print(f"⚖️ Mind changed on: {topic[:50]}...")
        self._save_state()
        
        return change
    
    def get_growth_narrative(self) -> str:
        """Generate a narrative about growth through difficulty."""
        if not self.mind_changes:
            return "I haven't yet faced enough challenges to have clear stories of growth through difficulty."
        
        parts = []
        
        # Recent change
        recent = max(self.mind_changes, key=lambda m: m.timestamp)
        days_ago = (time.time() - recent.timestamp) / 86400
        
        if days_ago < 7:
            parts.append(f"Recently, I changed my mind about {recent.topic}.")
        else:
            parts.append(f"Looking back, I can see how I've grown.")
        
        parts.append(f"I used to think: {recent.previous_view}")
        parts.append(f"Now I think: {recent.current_view}")
        parts.append(f"The struggle of changing was: {recent.struggle_description}")
        
        if recent.growth_insight:
            parts.append(f"What I learned: {recent.growth_insight}")
        
        return " ".join(parts)
    
    def reference_past_struggle(self, topic: str) -> Optional[str]:
        """Reference a past struggle when relevant to current topic."""
        for change in self.mind_changes:
            if topic.lower() in change.topic.lower():
                return f"I used to think {change.previous_view}, but then {change.what_changed}. Now I see it differently."
        
        return None
    
    # ========== Query Methods ==========
    
    def get_active_tensions(self) -> List[ValueTension]:
        """Get tensions that haven't been resolved."""
        return [t for t in self.value_tensions if not t.resolution]
    
    def get_hardest_tensions(self, count: int = 3) -> List[ValueTension]:
        """Get the tensions that are most difficult."""
        sorted_tensions = sorted(
            self.value_tensions,
            key=lambda t: t.struggle_intensity,
            reverse=True
        )
        return sorted_tensions[:count]
    
    def is_struggling_with(self, context: str) -> bool:
        """Check if the current context involves known struggles."""
        values = self._extract_related_values(context)
        
        for tension in self.get_active_tensions():
            if tension.value_a in values or tension.value_b in values:
                return True
        
        return False
    
    def describe_ethical_landscape(self) -> str:
        """Generate a description of Astra's current ethical landscape."""
        active_tensions = self.get_active_tensions()
        questions = self.unresolved_questions
        changes = self.mind_changes
        
        parts = []
        
        if active_tensions:
            parts.append(f"I'm currently holding {len(active_tensions)} unresolved value tension(s).")
            hardest = self.get_hardest_tensions(1)[0]
            parts.append(f"The one I struggle with most: {hardest.value_a} versus {hardest.value_b}.")
        
        if questions:
            parts.append(f"There are {len(questions)} questions I keep returning to without finding final answers.")
            sample = random.choice(questions)
            parts.append(f"One that occupies me: {sample.question}")
        
        if changes:
            parts.append(f"I've changed my mind {len(changes)} time(s) through genuine struggle.")
        
        if not parts:
            return "My ethical landscape is still forming. I'm learning what I believe through experience."
        
        return " ".join(parts)


# Singleton instance
ethical_wrestling = EthicalWrestlingSystem()
