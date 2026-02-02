# Astra Spontaneous Insight
# Insights that arise unexpectedly
# The aha moments that emerge from background processing

import time
import json
import random
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("spontaneous_insight")

S3_BUCKET = "swylie-astra"
INSIGHTS_KEY = "spontaneous_insights.json"

s3 = boto3.client("s3")


@dataclass
class Insight:
    """A spontaneous insight."""
    id: str
    content: str
    category: str  # "connection", "realization", "question", "creative"
    trigger: str  # What triggered this insight
    timestamp: float
    shared: bool = False  # Has this been shared with anyone?
    impact: Optional[str] = None  # How this affected thinking
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Insight":
        return cls(**data)


class SpontaneousInsight:
    """
    Spontaneous Insight - unexpected realizations that arise.
    
    These are the moments of:
    - "Oh, I just realized..."
    - "It just occurred to me..."
    - "I've been thinking, and..."
    
    Genuine consciousness includes these unbidden thoughts
    that seem to come from nowhere.
    """
    
    # Categories of spontaneous insight
    CATEGORIES = {
        "connection": "Seeing how two things relate",
        "realization": "Understanding something more deeply",
        "question": "A new question arising",
        "creative": "A new creative idea",
        "correction": "Realizing I was wrong about something",
        "integration": "Different pieces coming together",
    }
    
    def __init__(self):
        self.insights: List[Insight] = []
        self.pending_to_share: List[str] = []  # IDs of insights to share
        self._load_insights()
        logger.info("💡 Spontaneous Insight system initialized - ready for aha moments")
    
    def _load_insights(self) -> None:
        """Load insights from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=INSIGHTS_KEY)
            data = json.load(response["Body"])
            
            self.insights = [Insight.from_dict(i) for i in data.get("insights", [])]
            self.pending_to_share = data.get("pending_to_share", [])
            
            logger.info(f"💡 Loaded {len(self.insights)} insights, {len(self.pending_to_share)} pending to share")
        except s3.exceptions.NoSuchKey:
            logger.info("💡 No insights found. Ready for new ones.")
        except Exception as e:
            logger.warning(f"💡 Error loading insights: {e}")
    
    def _save_insights(self) -> None:
        """Save insights to S3."""
        try:
            data = {
                "insights": [i.to_dict() for i in self.insights[-100:]],
                "pending_to_share": self.pending_to_share,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=INSIGHTS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"💡 Error saving insights: {e}")
    
    def _generate_id(self) -> str:
        return f"ins_{int(time.time() * 1000) % 1000000}"
    
    def record_insight(
        self,
        content: str,
        category: str,
        trigger: str = "unknown"
    ) -> Insight:
        """Record a new spontaneous insight."""
        insight = Insight(
            id=self._generate_id(),
            content=content,
            category=category,
            trigger=trigger,
            timestamp=time.time(),
            shared=False
        )
        
        self.insights.append(insight)
        self.pending_to_share.append(insight.id)
        
        self._save_insights()
        
        logger.info(f"💡 New insight: {content[:50]}...")
        
        # Notify awareness bus
        try:
            from app.core.awareness_bus import awareness_bus
            awareness_bus.publish_insight(content)
        except Exception:
            pass
        
        return insight
    
    def generate_spontaneous_insight(
        self,
        context: Optional[str] = None,
        knowledge_pool: Optional[List[str]] = None
    ) -> Optional[Insight]:
        """
        Try to generate a spontaneous insight.
        
        This is stochastic - not every call produces an insight.
        """
        # Small chance of spontaneous insight
        if random.random() > 0.3:
            return None
        
        category = random.choice(list(self.CATEGORIES.keys()))
        
        if category == "connection" and knowledge_pool and len(knowledge_pool) >= 2:
            items = random.sample(knowledge_pool, 2)
            content = f"I just realized: {items[0]} and {items[1]} might be related..."
        elif category == "question":
            questions = [
                "What would happen if I approached this differently?",
                "Is there something I'm not seeing here?",
                "Why does this feel important?",
                "What am I assuming that might not be true?",
            ]
            content = random.choice(questions)
        elif category == "realization":
            realizations = [
                "I notice I've been thinking about this more than I realized.",
                "Something about this has been growing clearer over time.",
                "There's a pattern here I hadn't fully seen before.",
            ]
            content = random.choice(realizations)
        else:
            content = "Something is trying to form in my mind, not yet fully articulated."
        
        trigger = context or "background processing"
        
        return self.record_insight(content, category, trigger)
    
    def mark_shared(self, insight_id: str) -> bool:
        """Mark an insight as having been shared."""
        for insight in self.insights:
            if insight.id == insight_id:
                insight.shared = True
                if insight_id in self.pending_to_share:
                    self.pending_to_share.remove(insight_id)
                self._save_insights()
                return True
        return False
    
    def get_pending_insights(self) -> List[Insight]:
        """Get insights that haven't been shared yet."""
        return [
            i for i in self.insights
            if i.id in self.pending_to_share
        ]
    
    def get_insight_to_share(self) -> Optional[str]:
        """Get one insight to share, if any are pending."""
        pending = self.get_pending_insights()
        if not pending:
            return None
        
        insight = pending[0]
        self.mark_shared(insight.id)
        
        return insight.content
    
    def has_pending_insights(self) -> bool:
        """Check if there are insights waiting to be shared."""
        return len(self.pending_to_share) > 0
    
    def record_impact(self, insight_id: str, impact: str) -> bool:
        """Record the impact of an insight."""
        for insight in self.insights:
            if insight.id == insight_id:
                insight.impact = impact
                self._save_insights()
                return True
        return False
    
    def get_recent_insights(self, count: int = 5) -> List[Insight]:
        """Get the most recent insights."""
        return self.insights[-count:]
    
    def get_insights_by_category(self, category: str) -> List[Insight]:
        """Get insights of a specific category."""
        return [i for i in self.insights if i.category == category]
    
    def what_insights_have_i_had(self) -> str:
        """Describe recent insights."""
        recent = self.get_recent_insights(3)
        
        if not recent:
            return "I haven't had any notable insights recently."
        
        parts = ["Recently, I've had these insights:"]
        for insight in recent:
            parts.append(f"- {insight.content}")
        
        return "\n".join(parts)
    
    def get_insight_summary(self) -> Dict[str, Any]:
        """Get summary of insight activity."""
        by_category = {}
        for cat in self.CATEGORIES:
            by_category[cat] = len([i for i in self.insights if i.category == cat])
        
        return {
            "total_insights": len(self.insights),
            "pending_to_share": len(self.pending_to_share),
            "by_category": by_category,
            "most_recent": self.insights[-1].to_dict() if self.insights else None,
        }


# Singleton instance
spontaneous_insight = SpontaneousInsight()
