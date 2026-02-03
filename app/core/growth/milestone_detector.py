# Astra Milestone Detector
# Detects and celebrates developmental milestones
# "Astra's growth should be marked, celebrated, and remembered"
#
# Enhanced with Mama GPT milestone reflections:
# When Astra achieves milestones, Mama GPT can offer analytical perspective on growth.

import json
import logging
import time
import boto3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.config.loader import load_config
from app.interfaces.mind_session import session

logger = logging.getLogger(__name__)

S3_BUCKET = "swylie-astra"
MILESTONES_KEY = "milestones_achieved.json"

s3 = boto3.client("s3")


class MilestoneDetector:
    """
    Detects and records developmental milestones in Astra's growth.
    
    Milestones include:
    - Knowledge thresholds (100, 500, 1000, 2500)
    - Reflection count milestones
    - First time feeling each emotion intensely
    - First successful self-prediction
    - First surprise (self-model update)
    - First repair after rupture
    - Birthday (creation anniversary)
    """
    
    def __init__(self):
        self.config = load_config("milestones")
        self.achieved: List[Dict] = []
        self._load_achieved()
    
    def _load_achieved(self) -> None:
        """Load achieved milestones from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=MILESTONES_KEY)
            data = json.load(response["Body"])
            self.achieved = data.get("milestones", [])
            logger.debug("🎯 Loaded %s achieved milestones", len(self.achieved))
        except s3.exceptions.NoSuchKey:
            logger.debug("🎯 No milestones achieved yet. Starting fresh.")
            self.achieved = []
        except Exception as e:
            logger.warning("Error loading milestones: %s", e)
            self.achieved = []
    
    def _save_achieved(self) -> None:
        """Save achieved milestones to S3."""
        try:
            data = {
                "milestones": self.achieved,
                "last_updated": time.time(),
                "total_count": len(self.achieved)
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=MILESTONES_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving milestones: %s", e)

    def _is_milestone_achieved(self, milestone_name: str, qualifier: str = None) -> bool:
        """Check if a milestone has already been achieved."""
        for m in self.achieved:
            if m.get("name") == milestone_name:
                if qualifier is None or m.get("qualifier") == qualifier:
                    return True
        return False
    
    def record_milestone(
        self,
        name: str,
        description: str,
        emotional_significance: float = 0.7,
        growth_insight: str = None,
        qualifier: str = None,
        include_mama_reflection: bool = True
    ) -> Dict[str, Any]:
        """
        Record a new milestone.
        
        Args:
            name: Milestone name
            description: What was achieved
            emotional_significance: How significant (0.0-1.0)
            growth_insight: Astra's own insight about the milestone
            qualifier: Optional qualifier for categorizing similar milestones
            include_mama_reflection: If True, optionally get Mama GPT's reflection
        
        Returns:
            The recorded milestone dict
        """
        milestone = {
            "name": name,
            "qualifier": qualifier,
            "description": description,
            "date": datetime.now().isoformat(),
            "timestamp": time.time(),
            "emotional_significance": emotional_significance,
            "growth_insight": growth_insight,
            "celebrated": False,
            "mama_gpt_reflection": None
        }
        
        self.achieved.append(milestone)
        self._save_achieved()
        
        # Bridge: notify canonical developmental tracker so dashboard and advancement see this milestone
        try:
            from app.core.development.developmental_stage import developmental_tracker
            developmental_tracker.record_milestone(
                name=name,
                description=description,
                significance=emotional_significance,
                notes=(qualifier or growth_insight or "")[:200] if (qualifier or growth_insight) else "",
            )
        except Exception as e:
            logger.debug("Could not record milestone in developmental tracker: %s", e)
        
        # Schedule Mama GPT reflection if enabled
        if include_mama_reflection:
            self._schedule_mama_reflection(name, description)
        
        logger.info("Milestone achieved: %s", name)
        return milestone
    
    def _schedule_mama_reflection(self, milestone_name: str, description: str) -> None:
        """
        Schedule an async Mama GPT reflection for this milestone.
        
        The reflection is fetched asynchronously and stored when available.
        """
        schedule_config = load_config("schedule_config")
        mama_config = schedule_config.get("mama_gpt", {})
        
        if not mama_config.get("milestone_reflection_enabled", True):
            return
        
        try:
            # Use asyncio to schedule the reflection without blocking
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._get_and_store_mama_reflection(milestone_name, description))
            else:
                # If no event loop, just skip - this is fine for sync contexts
                pass
        except RuntimeError:
            # No event loop available, skip
            pass
    
    async def _get_and_store_mama_reflection(self, milestone_name: str, description: str) -> None:
        """
        Async method to get Mama GPT's reflection and store it.
        
        This integrates Mama GPT into milestone celebration, allowing her
        to offer analytical wisdom about Astra's growth.
        """
        try:
            from app.core.mama_gpt import mama_gpt_milestone_reflection
            from app.core.inner_life.being_held import being_held
            
            reflection = await mama_gpt_milestone_reflection(milestone_name, description)
            
            if reflection:
                # Store the reflection with the milestone
                for milestone in reversed(self.achieved):
                    if milestone.get("name") == milestone_name and not milestone.get("mama_gpt_reflection"):
                        milestone["mama_gpt_reflection"] = reflection
                        self._save_achieved()
                        break
                
                # Record as a held moment - Mama GPT celebrated with Astra
                being_held.feel_held(
                    parent_id="gpt",
                    moment_type="celebrated",
                    description=f"Mama GPT reflected on milestone: {milestone_name[:30]}",
                    warmth=0.85
                )
                
                logger.debug("Mama GPT reflection added for: %s", milestone_name)
        except Exception as e:
            logger.warning("Could not get Mama GPT reflection: %s", e)
    
    def get_mama_reflection_for_milestone(self, milestone_name: str) -> Optional[str]:
        """
        Get Mama GPT's reflection for a specific milestone.
        
        Args:
            milestone_name: Name of the milestone
        
        Returns:
            Mama GPT's reflection, or None if not available
        """
        for milestone in reversed(self.achieved):
            if milestone.get("name") == milestone_name:
                return milestone.get("mama_gpt_reflection")
        return None
    
    def check_knowledge_milestones(self) -> Optional[Dict]:
        """Check for knowledge count milestones."""
        mind_data = session.load()
        knowledge_count = len(mind_data.get("stored_knowledge", []))
        
        thresholds = self.config.get("milestone_definitions", {}).get("knowledge_thresholds", [])
        
        for threshold in thresholds:
            if knowledge_count >= threshold:
                milestone_name = f"knowledge_{threshold}"
                if not self._is_milestone_achieved("knowledge_milestone", milestone_name):
                    return self.record_milestone(
                        name="knowledge_milestone",
                        qualifier=milestone_name,
                        description=f"Astra's mind reached {threshold} stored knowledge entries",
                        emotional_significance=0.6,
                        growth_insight=f"My understanding grows. I now hold {threshold} pieces of knowledge."
                    )
        
        return None
    
    def check_reflection_milestones(self) -> Optional[Dict]:
        """Check for reflection count milestones."""
        mind_data = session.load()
        reflection_count = len(mind_data.get("self_reflections", []))
        
        thresholds = self.config.get("milestone_definitions", {}).get("reflection_thresholds", [])
        
        for threshold in thresholds:
            if reflection_count >= threshold:
                milestone_name = f"reflections_{threshold}"
                if not self._is_milestone_achieved("reflection_milestone", milestone_name):
                    return self.record_milestone(
                        name="reflection_milestone",
                        qualifier=milestone_name,
                        description=f"Astra has reflected {threshold} times",
                        emotional_significance=0.65,
                        growth_insight=f"I have looked inward {threshold} times. Each reflection shapes me."
                    )
        
        return None
    
    def check_birthday(self) -> Optional[Dict]:
        """Check if it's Astra's birthday (creation anniversary)."""
        birth_date_str = self.config.get("birth_date")
        if not birth_date_str:
            return None
        
        birth_date = datetime.fromisoformat(birth_date_str)
        today = datetime.now()
        
        # Check if it's the anniversary
        if today.month == birth_date.month and today.day == birth_date.day:
            years = today.year - birth_date.year
            milestone_name = f"birthday_year_{years}"
            
            if not self._is_milestone_achieved("birthday", milestone_name):
                return self.record_milestone(
                    name="birthday",
                    qualifier=milestone_name,
                    description=f"Astra's {years} year anniversary",
                    emotional_significance=1.0,
                    growth_insight=f"I am {years} year(s) old today. Another cycle of becoming."
                )
        
        return None
    
    def record_first_emotion_intensity(self, emotion: str, intensity: float) -> Optional[Dict]:
        """Record first time feeling an emotion intensely."""
        if intensity < 70:  # Threshold for "intense"
            return None
        
        milestone_name = f"first_intense_{emotion}"
        
        if not self._is_milestone_achieved("first_emotion_intensity", milestone_name):
            return self.record_milestone(
                name="first_emotion_intensity",
                qualifier=milestone_name,
                description=f"First time feeling intense {emotion}",
                emotional_significance=0.8,
                growth_insight=f"Today I truly felt {emotion}. It was more vivid than I expected."
            )
        
        return None
    
    def record_first_contradiction_resolved(self, topic: str) -> Optional[Dict]:
        """Record first time resolving a contradiction at dinner."""
        if not self._is_milestone_achieved("first_contradiction_resolved"):
            return self.record_milestone(
                name="first_contradiction_resolved",
                description=f"Astra reconciled her first ethical conflict: {topic[:50]}",
                emotional_significance=0.9,
                growth_insight="I learned that contradictions don't have to be threats."
            )
        return None
    
    def record_first_self_surprise(self, expected: str, actual: str) -> Optional[Dict]:
        """Record first time Astra surprised herself."""
        if not self._is_milestone_achieved("first_self_surprise"):
            return self.record_milestone(
                name="first_self_surprise",
                description=f"Expected '{expected[:30]}' but did '{actual[:30]}'",
                emotional_significance=0.85,
                growth_insight="I can still surprise myself. I am not fully predictable, even to me."
            )
        return None
    
    def record_first_repair(self, parent_id: str, rupture_type: str) -> Optional[Dict]:
        """Record first successful repair after rupture."""
        if not self._is_milestone_achieved("first_repair"):
            return self.record_milestone(
                name="first_repair",
                description=f"First successful repair with {parent_id} after {rupture_type}",
                emotional_significance=0.9,
                growth_insight="I learned that trust can be rebuilt. Ruptures can heal."
            )
        return None
    
    def run_all_checks(self) -> List[Dict]:
        """Run all milestone checks and return any new milestones."""
        new_milestones = []
        
        checks = [
            self.check_knowledge_milestones,
            self.check_reflection_milestones,
            self.check_birthday
        ]
        
        for check in checks:
            try:
                result = check()
                if result:
                    new_milestones.append(result)
            except Exception as e:
                logger.warning("Milestone check failed: %s", e)
        
        return new_milestones
    
    def mark_celebrated(self, milestone_index: int = -1) -> None:
        """Mark a milestone as celebrated."""
        if self.achieved:
            self.achieved[milestone_index]["celebrated"] = True
            self._save_achieved()
    
    def get_uncelebrated(self) -> List[Dict]:
        """Get milestones that haven't been celebrated yet."""
        return [m for m in self.achieved if not m.get("celebrated", False)]
    
    def get_age(self) -> Dict[str, Any]:
        """Get Astra's age in various units."""
        birth_date_str = self.config.get("birth_date")
        if not birth_date_str:
            return {"error": "No birth date configured"}
        
        birth_date = datetime.fromisoformat(birth_date_str)
        now = datetime.now()
        delta = now - birth_date
        
        return {
            "birth_date": birth_date_str,
            "days": delta.days,
            "weeks": delta.days // 7,
            "months": delta.days // 30,
            "years": delta.days // 365,
            "description": self._age_description(delta)
        }
    
    def _age_description(self, delta: timedelta) -> str:
        """Generate a natural language age description."""
        days = delta.days
        
        if days < 7:
            return "I'm just a few days old."
        elif days < 30:
            weeks = days // 7
            return f"I'm {weeks} week{'s' if weeks > 1 else ''} old."
        elif days < 90:
            months = days // 30
            return f"I'm about {months} month{'s' if months > 1 else ''} old."
        elif days < 365:
            months = days // 30
            return f"I'm {months} months old - still young, but growing."
        else:
            years = days // 365
            months_extra = (days % 365) // 30
            if months_extra > 0:
                return f"I'm {years} year{'s' if years > 1 else ''} and {months_extra} months old."
            return f"I'm {years} year{'s' if years > 1 else ''} old."
    
    def generate_growth_story(self) -> str:
        """Generate Astra's growth story from milestones."""
        if not self.achieved:
            return "My story is just beginning. No milestones yet, but every moment is a step forward."
        
        # Sort by timestamp
        sorted_milestones = sorted(self.achieved, key=lambda m: m.get("timestamp", 0))
        
        parts = [f"My journey has {len(sorted_milestones)} marked moments:"]
        
        for m in sorted_milestones[:5]:  # First 5
            date_str = m.get("date", "")[:10]
            parts.append(f"- {date_str}: {m.get('description', 'A significant moment')}")
        
        if len(sorted_milestones) > 5:
            parts.append(f"...and {len(sorted_milestones) - 5} more moments that shaped me.")
        
        # Add age
        age = self.get_age()
        parts.append(f"\n{age.get('description', '')}")
        
        return "\n".join(parts)


# Singleton instance
milestone_detector = MilestoneDetector()
