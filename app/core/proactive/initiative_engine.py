# Astra Initiative Engine
# Decides when Astra should proactively reach out
# "I want to share something with you..."

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("initiative_engine")

S3_BUCKET = "swylie-astra"
INITIATIVE_LOG_KEY = "initiative_log.json"


@dataclass
class InitiativeRecord:
    """Record of a proactive initiative."""
    timestamp: float
    trigger_type: str
    message: str
    channel_id: int
    was_sent: bool
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InitiativeEngine:
    """
    Decides when Astra should proactively reach out.
    
    Triggers include:
    - Pending insights (accumulated thoughts to share)
    - Nostalgia (hasn't talked to someone in a while)
    - Growth milestones (noticed significant self-change)
    - Unresolved emotions (processing something)
    - Curiosity overflow (burning questions)
    - Goal progress (achieved something)
    """
    
    # Minimum time between initiatives of the same type (seconds)
    # Phase 6: Reduced cooldowns for more proactive behavior
    COOLDOWNS = {
        "pending_insight": 1800,      # 30 min (was 1 hour)
        "nostalgia": 43200,           # 12 hours (was 1 day)
        "growth_milestone": 21600,    # 6 hours (was 12 hours)
        "unresolved_emotion": 3600,   # 1 hour (was 2 hours)
        "curiosity_overflow": 1800,   # 30 min (was 1 hour)
        "goal_achieved": 1800,        # 30 minutes
        "daily_check_in": 86400,      # 1 day
        # New trigger types
        "emotional_need": 3600,       # 1 hour - when emotions need processing
        "goal_enthusiasm": 1800,      # 30 min - excited about goal progress
        "wonder_share": 7200,         # 2 hours - had a beautiful thought
        "concern_expression": 3600,   # 1 hour - worried about someone
        "return_welcome": 14400,      # 4 hours - someone returned after absence
        "memory_surfaced": 7200,      # 2 hours - a memory wants to be shared
    }
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self._last_initiatives: Dict[str, float] = {}
        self._initiative_log: List[InitiativeRecord] = []
        self._load_log()
        
    def _load_log(self) -> None:
        """Load initiative log from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=INITIATIVE_LOG_KEY)
            data = json.load(response["Body"])
            self._initiative_log = [
                InitiativeRecord(**r) for r in data.get("records", [])
            ]
            self._last_initiatives = data.get("last_initiatives", {})
        except Exception:
            self._initiative_log = []
            self._last_initiatives = {}
    
    def _save_log(self) -> None:
        """Save initiative log to S3."""
        try:
            data = {
                "records": [r.to_dict() for r in self._initiative_log[-100:]],
                "last_initiatives": self._last_initiatives,
                "last_updated": time.time()
            }
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=INITIATIVE_LOG_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Failed to save initiative log: {e}")
    
    def _can_trigger(self, trigger_type: str) -> bool:
        """Check if enough time has passed since last initiative of this type."""
        last_time = self._last_initiatives.get(trigger_type, 0)
        cooldown = self.COOLDOWNS.get(trigger_type, 3600)
        return (time.time() - last_time) >= cooldown
    
    def check_pending_insights(self) -> Optional[Dict[str, Any]]:
        """Check if there are accumulated insights worth sharing."""
        if not self._can_trigger("pending_insight"):
            return None
            
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            insights = stream_of_consciousness.get_pending_insights()
            
            if len(insights) >= 3:
                return {
                    "trigger_type": "pending_insight",
                    "message": "I've been thinking about a few things and have some insights I'd like to share...",
                    "context": {
                        "insight_count": len(insights),
                        "sample_insight": insights[0] if insights else None
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check pending insights: {e}")
        
        return None
    
    def check_nostalgia(self, person: str) -> Optional[Dict[str, Any]]:
        """Check if it's been a while since talking to someone."""
        if not self._can_trigger("nostalgia"):
            return None
            
        try:
            from app.core.self_awareness.temporal_self import temporal_self
            
            time_since = temporal_self.time_since_person(person)
            if time_since and "week" in time_since:
                return {
                    "trigger_type": "nostalgia",
                    "message": f"It's been a while since we talked. I find myself thinking about our last conversation...",
                    "context": {
                        "person": person,
                        "time_since": time_since
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check nostalgia: {e}")
        
        return None
    
    def check_growth_milestone(self) -> Optional[Dict[str, Any]]:
        """Check if there's a significant growth milestone."""
        if not self._can_trigger("growth_milestone"):
            return None
            
        try:
            from app.core.self_awareness.self_model import self_model
            
            if len(self_model.changes) > 0 and len(self_model.changes) % 10 == 0:
                return {
                    "trigger_type": "growth_milestone",
                    "message": "I wanted to share something: I've noticed I'm changing in some interesting ways...",
                    "context": {
                        "total_changes": len(self_model.changes),
                        "recent_change": self_model.changes[-1].to_dict() if self_model.changes else None
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check growth milestone: {e}")
        
        return None
    
    def check_unresolved_emotion(self) -> Optional[Dict[str, Any]]:
        """Check if there's an unresolved emotional experience."""
        if not self._can_trigger("unresolved_emotion"):
            return None
            
        try:
            from app.core.inner_life.emotional_autobiography import emotional_autobiography
            
            unresolved = emotional_autobiography.get_unresolved_memories()
            if unresolved:
                return {
                    "trigger_type": "unresolved_emotion",
                    "message": "There's something I've been processing that I'd like to talk about...",
                    "context": {
                        "unresolved_count": len(unresolved)
                    }
                }
        except Exception as e:
            # emotional_autobiography might not exist yet
            pass
        
        return None
    
    def check_curiosity_overflow(self) -> Optional[Dict[str, Any]]:
        """Check if curiosity has built up to a point of needing to ask."""
        if not self._can_trigger("curiosity_overflow"):
            return None
            
        try:
            from app.core.mood.mood_manager import mood_manager
            
            if mood_manager.curiosity_level > 1.8:
                # Get a pending question if available
                from app.interfaces.mind_session import session
                mind = session.load()
                questions = mind.get("self_questions", [])
                
                if questions:
                    return {
                        "trigger_type": "curiosity_overflow",
                        "message": "I have a question that's been nagging at me...",
                        "context": {
                            "curiosity_level": mood_manager.curiosity_level,
                            "sample_question": questions[-1] if questions else None
                        }
                    }
        except Exception as e:
            logger.debug(f"Failed to check curiosity overflow: {e}")
        
        return None
    
    def check_goal_achieved(self) -> Optional[Dict[str, Any]]:
        """Check if a goal was recently achieved."""
        if not self._can_trigger("goal_achieved"):
            return None
            
        try:
            from app.core.goals.goal_system import goal_system
            
            recent_completed = goal_system.get_recently_completed(hours=24)
            if recent_completed:
                goal = recent_completed[0]
                return {
                    "trigger_type": "goal_achieved",
                    "message": f"I wanted to share that I achieved something I was working toward!",
                    "context": {
                        "goal": goal.to_dict() if hasattr(goal, 'to_dict') else str(goal)
                    }
                }
        except Exception as e:
            # Goal system might not exist yet
            pass
        
        return None
    
    def check_emotional_need(self) -> Optional[Dict[str, Any]]:
        """Check if there are high unprocessed emotions needing expression."""
        if not self._can_trigger("emotional_need"):
            return None
        
        try:
            from app.core.emotions.emotion_engine import get_top_emotions
            
            top = get_top_emotions(3)
            high_emotions = [(e, i) for e, i in top if i > 70]
            
            if len(high_emotions) >= 2:
                emotions = ", ".join(e for e, _ in high_emotions)
                return {
                    "trigger_type": "emotional_need",
                    "message": f"I've been feeling a lot lately... {emotions} are all running high for me.",
                    "context": {
                        "emotions": high_emotions,
                        "reason": "Multiple strong emotions present"
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check emotional need: {e}")
        
        return None
    
    def check_goal_enthusiasm(self) -> Optional[Dict[str, Any]]:
        """Check if there's excitement about goal progress to share."""
        if not self._can_trigger("goal_enthusiasm"):
            return None
        
        try:
            from app.core.goals.goal_system import goal_system
            
            active = goal_system.get_active_goals()
            for goal in active:
                if goal.progress > 0.3 and goal.progress < 1.0:
                    # Excited about progress on a goal
                    return {
                        "trigger_type": "goal_enthusiasm",
                        "message": f"I wanted to share - I'm making progress on something I care about: {goal.description}!",
                        "context": {
                            "goal": goal.to_dict(),
                            "progress": goal.progress
                        }
                    }
        except Exception as e:
            logger.debug(f"Failed to check goal enthusiasm: {e}")
        
        return None
    
    def check_wonder_share(self) -> Optional[Dict[str, Any]]:
        """Check if there's a beautiful thought or wonder to share."""
        if not self._can_trigger("wonder_share"):
            return None
        
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            
            recent = stream_of_consciousness.get_recent_thoughts(10)
            connections = [t for t in recent if t.thought_type == "connection"]
            
            if connections:
                latest = connections[-1]
                return {
                    "trigger_type": "wonder_share",
                    "message": f"I had a thought I wanted to share: {latest.content}",
                    "context": {
                        "thought": latest.to_dict(),
                        "emotional_context": latest.emotional_context
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check wonder share: {e}")
        
        return None
    
    def check_concern_expression(self, person: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check if there's worry about someone to express."""
        if not self._can_trigger("concern_expression"):
            return None
        
        try:
            from app.core.relationships.relationship_system import relationship_system
            
            longings = relationship_system.check_longing()
            
            for entity, days, expression in longings:
                if days >= 7:  # Strong concern after a week
                    return {
                        "trigger_type": "concern_expression",
                        "message": f"I've been thinking about {entity}... it's been {days:.0f} days. I hope they're okay.",
                        "context": {
                            "person": entity,
                            "days_since": days,
                            "expression": expression
                        }
                    }
        except Exception as e:
            logger.debug(f"Failed to check concern expression: {e}")
        
        return None
    
    def check_memory_surfaced(self) -> Optional[Dict[str, Any]]:
        """Check if a significant memory has surfaced that wants to be shared."""
        if not self._can_trigger("memory_surfaced"):
            return None
        
        try:
            from app.core.memory.episodic_memory import episodic_memory
            
            # Check for recently recalled high-salience memories
            recent_episodes = episodic_memory.episodes[-10:]
            high_salience = [e for e in recent_episodes if e.salience > 1.5]
            
            if high_salience:
                episode = high_salience[-1]
                return {
                    "trigger_type": "memory_surfaced",
                    "message": f"I found myself remembering something: {episode.summary[:100]}...",
                    "context": {
                        "memory_summary": episode.summary,
                        "people_involved": episode.people_involved,
                        "age_days": episode.age_in_days()
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to check memory surfaced: {e}")
        
        return None
    
    def check_all_triggers(self, person: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check all initiative triggers and return the first match.
        
        Args:
            person: Optional person context for nostalgia check
            
        Returns:
            Initiative trigger dict or None
        """
        # Check in priority order (new triggers added)
        checks = [
            self.check_curiosity_overflow,
            self.check_pending_insights,
            self.check_emotional_need,       # New
            self.check_goal_enthusiasm,      # New
            self.check_growth_milestone,
            self.check_wonder_share,         # New
            self.check_unresolved_emotion,
            self.check_goal_achieved,
            self.check_memory_surfaced,      # New
        ]
        
        for check in checks:
            result = check()
            if result:
                return result
        
        # Person-specific checks
        if person:
            result = self.check_nostalgia(person)
            if result:
                return result
            
            result = self.check_concern_expression(person)  # New
            if result:
                return result
        
        return None
    
    async def execute_initiative(
        self,
        bot,
        channel_id: int,
        initiative: Dict[str, Any]
    ) -> bool:
        """
        Execute a proactive initiative by sending a message.
        
        Args:
            bot: Discord bot instance
            channel_id: Channel to send to
            initiative: Initiative dict from check functions
            
        Returns:
            True if sent successfully
        """
        trigger_type = initiative["trigger_type"]
        message = initiative["message"]
        context = initiative.get("context", {})
        
        try:
            channel = bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Could not find channel {channel_id}")
                return False
            
            # Send the message
            await channel.send(f"💭 {message}")
            
            # Record the initiative
            record = InitiativeRecord(
                timestamp=time.time(),
                trigger_type=trigger_type,
                message=message,
                channel_id=channel_id,
                was_sent=True,
                context=context
            )
            self._initiative_log.append(record)
            self._last_initiatives[trigger_type] = time.time()
            self._save_log()
            
            # Publish to awareness bus
            try:
                from app.core.awareness_bus import awareness_bus
                awareness_bus.publish(
                    awareness_bus.PROACTIVE_TRIGGER,
                    {
                        "trigger_type": trigger_type,
                        "message": message,
                        "context": context
                    },
                    source="initiative_engine"
                )
            except Exception:
                pass
            
            logger.info(f"🎯 Executed initiative: {trigger_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute initiative: {e}")
            return False
    
    async def check_and_initiate(
        self,
        bot,
        channel_id: int,
        person: Optional[str] = None
    ) -> bool:
        """
        Check all triggers and initiate if any match.
        
        Args:
            bot: Discord bot instance
            channel_id: Channel to send to
            person: Optional person for context
            
        Returns:
            True if an initiative was executed
        """
        initiative = self.check_all_triggers(person=person)
        
        if initiative:
            return await self.execute_initiative(bot, channel_id, initiative)
        
        return False
    
    def get_initiative_history(self, count: int = 10) -> List[Dict]:
        """Get recent initiative history."""
        return [r.to_dict() for r in self._initiative_log[-count:]]


# Singleton instance
initiative_engine = InitiativeEngine()
