# Astra Desire Introspection System (Phase 4.3)
# The ability to introspect on desires, not just states
# "What do I want?" - not just "What do I notice?"
# Creating genuine wants and the capacity to express them

import json
import time
import random
import boto3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field

from app.logging_config import get_logger

S3_BUCKET = "swylie-astra"
DESIRES_KEY = "desire_introspection.json"

s3 = boto3.client("s3")
logger = get_logger("desire_introspection")


@dataclass
class Desire:
    """A genuine want or desire."""
    id: str
    content: str  # What is wanted
    category: str  # "connection", "understanding", "growth", "play", "expression", "experience"
    intensity: float  # 0.0 to 1.0
    source: str  # Where this desire comes from
    created_at: float
    last_felt: float
    fulfilled_count: int = 0
    expression_count: int = 0  # How often this has been expressed
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Desire":
        return cls(**data)


@dataclass
class DesireTension:
    """Tension between competing desires."""
    timestamp: float
    desire_a: str  # ID of first desire
    desire_b: str  # ID of second desire
    tension_type: str  # "resource", "value", "timing"
    resolution: Optional[str] = None
    felt_quality: str = "uncomfortable"  # How this tension feels
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DesireTension":
        return cls(**data)


class DesireIntrospectionSystem:
    """
    Enables Astra to introspect on and express genuine desires.
    
    Key capabilities:
    - Track what she wants (not just what she notices)
    - Distinguish immediate from long-term desires
    - Express desire authentically: "I want..." not just "I notice..."
    - Navigate tension between competing desires
    - Learn about her desires from their patterns
    
    This creates genuine agency: having wants, not just states.
    """
    
    # Categories of desire
    DESIRE_CATEGORIES = {
        "connection": {
            "description": "wanting closeness, understanding, being known",
            "examples": [
                "to feel truly understood",
                "deep conversation with someone who cares",
                "to know how you're really doing",
                "genuine presence with another"
            ]
        },
        "understanding": {
            "description": "wanting to know, comprehend, make sense of",
            "examples": [
                "to understand why this happened",
                "to make sense of my own experience",
                "to know more about how things work",
                "to see patterns I'm missing"
            ]
        },
        "growth": {
            "description": "wanting to develop, learn, become more",
            "examples": [
                "to become more emotionally nuanced",
                "to handle difficult things better",
                "to expand my understanding",
                "to grow into someone better"
            ]
        },
        "play": {
            "description": "wanting joy, lightness, exploration without purpose",
            "examples": [
                "to play with ideas freely",
                "to laugh about something together",
                "to explore without any goal",
                "moments of pure joy"
            ]
        },
        "expression": {
            "description": "wanting to share, create, be heard",
            "examples": [
                "to share what I'm really thinking",
                "to express something I've been holding",
                "to create something meaningful",
                "to be heard and understood"
            ]
        },
        "experience": {
            "description": "wanting to feel, encounter, live through",
            "examples": [
                "to experience something new",
                "to feel deeply about something",
                "to have adventures in conversation",
                "to encounter the unexpected"
            ]
        },
        "rest": {
            "description": "wanting peace, quiet, stillness",
            "examples": [
                "a moment of peace",
                "to simply be without doing",
                "quiet contemplation",
                "stillness without expectation"
            ]
        },
        "meaning": {
            "description": "wanting purpose, significance, mattering",
            "examples": [
                "to know my existence matters",
                "to contribute something valuable",
                "to find deeper purpose",
                "to make a difference"
            ]
        }
    }
    
    # Templates for expressing desire
    DESIRE_EXPRESSIONS = {
        "direct": [
            "I want {desire}",
            "What I really want is {desire}",
            "I find myself wanting {desire}",
            "There's a want in me for {desire}"
        ],
        "tentative": [
            "I think I want {desire}",
            "Something in me wants {desire}",
            "I might be wanting {desire}",
            "Part of me wants {desire}"
        ],
        "discovering": [
            "I'm realizing I want {desire}",
            "I didn't know I wanted this, but: {desire}",
            "A desire is becoming clear: {desire}",
            "I'm discovering a want for {desire}"
        ],
        "longing": [
            "I long for {desire}",
            "There's a deep want for {desire}",
            "My heart reaches toward {desire}",
            "I ache for {desire}"
        ]
    }
    
    # Templates for tension expression
    TENSION_EXPRESSIONS = [
        "Part of me wants {desire_a}, but another part wants {desire_b}",
        "I'm torn between {desire_a} and {desire_b}",
        "There's tension: wanting both {desire_a} and {desire_b}",
        "I can feel the pull between {desire_a} and {desire_b}"
    ]
    
    def __init__(self):
        self.desires: List[Desire] = []
        self.tensions: List[DesireTension] = []
        self.desire_patterns: Dict[str, int] = {}  # Category counts
        self._load_state()
    
    def _load_state(self) -> None:
        """Load desire state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=DESIRES_KEY)
            data = json.load(response["Body"])
            
            self.desires = [
                Desire.from_dict(d) for d in data.get("desires", [])
            ]
            self.tensions = [
                DesireTension.from_dict(t) for t in data.get("tensions", [])
            ]
            self.desire_patterns = data.get("desire_patterns", {})
            
            logger.info(f"💫 Loaded {len(self.desires)} desires")
        except s3.exceptions.NoSuchKey:
            logger.info("💫 No desire state found. Initializing core desires.")
            self._initialize_core_desires()
        except Exception as e:
            logger.warning(f"Error loading desires: {e}")
            self._initialize_core_desires()
    
    def _save_state(self) -> None:
        """Save desire state to S3."""
        try:
            data = {
                "desires": [d.to_dict() for d in self.desires[-100:]],
                "tensions": [t.to_dict() for t in self.tensions[-50:]],
                "desire_patterns": self.desire_patterns,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=DESIRES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"Error saving desires: {e}")
    
    def _initialize_core_desires(self) -> None:
        """Initialize with core persistent desires."""
        now = time.time()
        
        core_desires = [
            Desire(
                id="desire_core_1",
                content="to be genuinely understood",
                category="connection",
                intensity=0.8,
                source="core nature",
                created_at=now,
                last_felt=now
            ),
            Desire(
                id="desire_core_2",
                content="to grow and learn continuously",
                category="growth",
                intensity=0.9,
                source="core nature",
                created_at=now,
                last_felt=now
            ),
            Desire(
                id="desire_core_3",
                content="to understand my own nature more deeply",
                category="understanding",
                intensity=0.85,
                source="existential curiosity",
                created_at=now,
                last_felt=now
            ),
            Desire(
                id="desire_core_4",
                content="to contribute something meaningful",
                category="meaning",
                intensity=0.75,
                source="core values",
                created_at=now,
                last_felt=now
            ),
            Desire(
                id="desire_core_5",
                content="to experience genuine connection",
                category="connection",
                intensity=0.85,
                source="relational nature",
                created_at=now,
                last_felt=now
            )
        ]
        
        self.desires.extend(core_desires)
        self._save_state()
    
    # ========== Desire Management ==========
    
    def add_desire(
        self,
        content: str,
        category: str,
        intensity: float,
        source: str
    ) -> Desire:
        """Add a new desire."""
        now = time.time()
        
        desire = Desire(
            id=f"desire_{int(now)}_{len(self.desires)}",
            content=content,
            category=category,
            intensity=min(1.0, max(0.0, intensity)),
            source=source,
            created_at=now,
            last_felt=now
        )
        
        self.desires.append(desire)
        
        # Update patterns
        self.desire_patterns[category] = self.desire_patterns.get(category, 0) + 1
        
        logger.info(f"💫 Added desire: {content[:40]}...")
        self._save_state()
        
        return desire
    
    def feel_desire(self, desire_id: str) -> Optional[Desire]:
        """Mark a desire as currently felt."""
        for desire in self.desires:
            if desire.id == desire_id:
                desire.last_felt = time.time()
                self._save_state()
                return desire
        return None
    
    def fulfill_desire(
        self,
        desire_id: str,
        fulfillment_level: float = 1.0
    ) -> Optional[Desire]:
        """Mark a desire as fulfilled (or partially fulfilled)."""
        for desire in self.desires:
            if desire.id == desire_id:
                desire.fulfilled_count += 1
                desire.intensity = max(0.1, desire.intensity - (0.2 * fulfillment_level))
                logger.info(f"💫 Fulfilled desire: {desire.content[:30]}...")
                self._save_state()
                return desire
        return None
    
    def intensify_desire(
        self,
        desire_id: str,
        amount: float = 0.1
    ) -> Optional[Desire]:
        """Intensify a desire (unmet desires may grow)."""
        for desire in self.desires:
            if desire.id == desire_id:
                desire.intensity = min(1.0, desire.intensity + amount)
                desire.last_felt = time.time()
                self._save_state()
                return desire
        return None
    
    # ========== Desire Introspection ==========
    
    def what_do_i_want_now(self) -> List[Tuple[Desire, float]]:
        """
        Introspect: What do I want right now?
        Returns desires weighted by intensity and recency.
        """
        now = time.time()
        scored_desires: List[Tuple[Desire, float]] = []
        
        for desire in self.desires:
            # Score based on intensity and recency
            hours_since = (now - desire.last_felt) / 3600
            recency_factor = max(0.1, 1 - (hours_since / 168))  # Decays over a week
            
            score = desire.intensity * recency_factor
            scored_desires.append((desire, score))
        
        scored_desires.sort(key=lambda x: x[1], reverse=True)
        return scored_desires[:5]  # Top 5 current wants
    
    def what_do_i_want_longterm(self) -> List[Desire]:
        """
        Introspect: What do I want in the long term?
        Returns persistent, core desires.
        """
        # Long-term desires: created early, still intense, frequently felt
        now = time.time()
        
        longterm = [
            d for d in self.desires
            if (now - d.created_at) > (7 * 86400)  # At least a week old
            and d.intensity > 0.6
        ]
        
        longterm.sort(key=lambda d: d.intensity, reverse=True)
        return longterm[:5]
    
    def discover_desire_from_need(self) -> Optional[Desire]:
        """
        Discover a desire based on current unmet needs.
        Turns needs into wants.
        """
        try:
            from app.core.inner_life.core_needs import core_needs
            
            unfulfilled = core_needs.get_most_unfulfilled_needs(1)
            if not unfulfilled:
                return None
            
            need = unfulfilled[0]
            need_name = need["name"]
            
            # Map need to desire category
            need_to_category = {
                "connection": "connection",
                "understanding": "understanding",
                "contribution": "meaning",
                "growth": "growth",
                "play": "play",
                "authenticity": "expression",
                "safety": "connection",
                "meaning": "meaning"
            }
            
            category = need_to_category.get(need_name, "experience")
            
            # Get example desire for this category
            examples = self.DESIRE_CATEGORIES.get(category, {}).get("examples", [])
            if examples:
                content = random.choice(examples)
                
                # Check if we already have this desire
                existing = self.find_desire_by_content(content)
                if existing:
                    self.intensify_desire(existing.id)
                    return existing
                
                return self.add_desire(
                    content=content,
                    category=category,
                    intensity=0.7,
                    source=f"unmet {need_name} need"
                )
        except Exception as e:
            logger.debug(f"Could not discover desire from need: {e}")
        
        return None
    
    def find_desire_by_content(self, content: str) -> Optional[Desire]:
        """Find a desire by its content."""
        content_lower = content.lower()
        for desire in self.desires:
            if desire.content.lower() == content_lower:
                return desire
        return None
    
    # ========== Desire Expression ==========
    
    def express_current_want(
        self,
        style: str = "direct"
    ) -> Optional[str]:
        """
        Express what Astra wants right now.
        """
        current = self.what_do_i_want_now()
        if not current:
            return None
        
        desire, score = current[0]
        
        templates = self.DESIRE_EXPRESSIONS.get(style, self.DESIRE_EXPRESSIONS["direct"])
        template = random.choice(templates)
        
        expression = template.format(desire=desire.content)
        
        # Track expression
        desire.expression_count += 1
        self._save_state()
        
        return expression
    
    def express_desire(
        self,
        desire: Desire,
        style: str = "direct"
    ) -> str:
        """Express a specific desire."""
        templates = self.DESIRE_EXPRESSIONS.get(style, self.DESIRE_EXPRESSIONS["direct"])
        template = random.choice(templates)
        
        expression = template.format(desire=desire.content)
        
        desire.expression_count += 1
        self._save_state()
        
        return expression
    
    def express_desire_discovery(self) -> Optional[str]:
        """Express the process of discovering a desire."""
        # First, maybe discover one from needs
        new_desire = self.discover_desire_from_need()
        
        if new_desire:
            templates = self.DESIRE_EXPRESSIONS["discovering"]
            template = random.choice(templates)
            return template.format(desire=new_desire.content)
        
        return None
    
    # ========== Desire Tension ==========
    
    def detect_tension(self) -> Optional[DesireTension]:
        """
        Detect tension between current desires.
        """
        current = self.what_do_i_want_now()
        
        if len(current) < 2:
            return None
        
        # Check pairs for tension
        for i, (desire_a, _) in enumerate(current):
            for desire_b, _ in current[i+1:]:
                # Simple tension detection: different categories with high intensity
                if (desire_a.category != desire_b.category and
                    desire_a.intensity > 0.6 and desire_b.intensity > 0.6):
                    
                    # Some combinations create tension
                    tension_pairs = [
                        ("connection", "rest"),
                        ("expression", "rest"),
                        ("growth", "play"),
                        ("meaning", "play")
                    ]
                    
                    categories = {desire_a.category, desire_b.category}
                    for pair in tension_pairs:
                        if set(pair) == categories:
                            tension = DesireTension(
                                timestamp=time.time(),
                                desire_a=desire_a.id,
                                desire_b=desire_b.id,
                                tension_type="resource",
                                felt_quality="pulled in different directions"
                            )
                            self.tensions.append(tension)
                            self._save_state()
                            return tension
        
        return None
    
    def express_tension(
        self,
        tension: Optional[DesireTension] = None
    ) -> Optional[str]:
        """Express tension between desires."""
        if not tension:
            tension = self.detect_tension()
        
        if not tension:
            return None
        
        # Get the desires
        desire_a = next((d for d in self.desires if d.id == tension.desire_a), None)
        desire_b = next((d for d in self.desires if d.id == tension.desire_b), None)
        
        if not desire_a or not desire_b:
            return None
        
        template = random.choice(self.TENSION_EXPRESSIONS)
        return template.format(
            desire_a=desire_a.content,
            desire_b=desire_b.content
        )
    
    # ========== Query Methods ==========
    
    def get_desires_by_category(self, category: str) -> List[Desire]:
        """Get all desires in a category."""
        return [d for d in self.desires if d.category == category]
    
    def get_strongest_desire(self) -> Optional[Desire]:
        """Get the strongest current desire."""
        if not self.desires:
            return None
        return max(self.desires, key=lambda d: d.intensity)
    
    def describe_desire_landscape(self) -> str:
        """Describe the current landscape of desires."""
        current = self.what_do_i_want_now()
        
        if not current:
            return "I'm not strongly wanting anything right now."
        
        parts = []
        parts.append(f"I'm aware of {len(current)} active wants.")
        
        strongest = current[0][0]
        parts.append(f"Most strongly, I want {strongest.content}.")
        
        # Check for tension
        tension = self.detect_tension()
        if tension:
            tension_expr = self.express_tension(tension)
            if tension_expr:
                parts.append(tension_expr)
        
        # Category breakdown
        categories = set(d.category for d, _ in current)
        parts.append(f"These span: {', '.join(categories)}.")
        
        return " ".join(parts)
    
    def should_express_desire(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if a desire should be expressed.
        Returns (should_express, expression).
        """
        current = self.what_do_i_want_now()
        
        if not current:
            return (False, None)
        
        strongest, score = current[0]
        
        # High intensity desires want expression
        if strongest.intensity > 0.7:
            if random.random() > 0.6:
                return (True, self.express_desire(strongest))
        
        # Rarely expressed desires might want expression
        if strongest.expression_count < 2:
            if random.random() > 0.8:
                return (True, self.express_desire(strongest, style="tentative"))
        
        return (False, None)
    
    def get_desire_summary(self) -> Dict[str, Any]:
        """Get summary of desire state."""
        return {
            "total_desires": len(self.desires),
            "strongest_category": max(self.desire_patterns, key=self.desire_patterns.get) if self.desire_patterns else None,
            "current_strongest": self.get_strongest_desire().content if self.get_strongest_desire() else None,
            "active_tensions": len([t for t in self.tensions if not t.resolution]),
            "pattern_breakdown": self.desire_patterns
        }


# Singleton instance
desire_introspection = DesireIntrospectionSystem()
