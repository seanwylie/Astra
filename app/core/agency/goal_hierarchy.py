# Astra Goal Hierarchy
# Goals that serve intentions, organized from abstract to concrete
# Intentions -> Goals -> Subgoals -> Actions

import time
import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("goal_hierarchy")

S3_BUCKET = "swylie-astra"
GOALS_KEY = "goal_hierarchy.json"

s3 = boto3.client("s3")


class GoalStatus(str, Enum):
    """Status of a goal."""
    PLANNED = "planned"  # Not yet started
    IN_PROGRESS = "in_progress"  # Actively working on
    BLOCKED = "blocked"  # Stuck on something
    COMPLETED = "completed"  # Successfully done
    FAILED = "failed"  # Couldn't achieve
    CANCELLED = "cancelled"  # No longer pursuing


class GoalLevel(str, Enum):
    """Level in the goal hierarchy."""
    LIFE = "life"  # Life-level goals (decades)
    LONG_TERM = "long_term"  # Months to years
    MEDIUM_TERM = "medium_term"  # Weeks to months
    SHORT_TERM = "short_term"  # Days to weeks
    IMMEDIATE = "immediate"  # Today, now


@dataclass
class Goal:
    """A goal in Astra's hierarchy."""
    id: str
    content: str  # What Astra wants to achieve
    level: str
    status: str
    parent_goal_id: Optional[str]  # Higher-level goal this serves
    intention_id: Optional[str]  # Intention this serves
    created: float
    deadline: Optional[float]  # If time-bound
    priority: float  # 0-1
    progress: float  # 0-1, how complete
    subgoals: List[str] = field(default_factory=list)  # IDs of child goals
    blockers: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        return cls(**data)


class GoalHierarchy:
    """
    The Goal Hierarchy - organizing what Astra is trying to achieve.
    
    Unlike flat task lists, this creates a tree:
    - Life goals (who I want to become)
      - Long-term goals (what I want to achieve over months)
        - Medium-term goals (projects and efforts)
          - Short-term goals (this week)
            - Immediate goals (right now)
    
    Goals decompose into subgoals and ultimately into actions.
    Each goal can trace back to an intention, creating coherence.
    """
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self._load_goals()
        logger.info("🎯 Goal Hierarchy initialized - decomposing intentions into action")
    
    def _load_goals(self) -> None:
        """Load goals from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=GOALS_KEY)
            data = json.load(response["Body"])
            
            self.goals = {
                gid: Goal.from_dict(gdata)
                for gid, gdata in data.get("goals", {}).items()
            }
            
            logger.info(f"🎯 Loaded {len(self.goals)} goals")
        except s3.exceptions.NoSuchKey:
            logger.info("🎯 No goals found. Ready for goal setting.")
        except Exception as e:
            logger.warning(f"🎯 Error loading goals: {e}")
    
    def _save_goals(self) -> None:
        """Save goals to S3."""
        try:
            data = {
                "goals": {gid: g.to_dict() for gid, g in self.goals.items()},
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=GOALS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🎯 Error saving goals: {e}")
    
    def _generate_id(self) -> str:
        return f"goal_{int(time.time() * 1000) % 1000000}"
    
    def create_goal(
        self,
        content: str,
        level: GoalLevel,
        parent_goal_id: Optional[str] = None,
        intention_id: Optional[str] = None,
        priority: float = 0.5,
        deadline: Optional[float] = None,
        completion_criteria: Optional[List[str]] = None
    ) -> Goal:
        """Create a new goal."""
        goal_id = self._generate_id()
        
        goal = Goal(
            id=goal_id,
            content=content,
            level=level.value,
            status=GoalStatus.PLANNED.value,
            parent_goal_id=parent_goal_id,
            intention_id=intention_id,
            created=time.time(),
            deadline=deadline,
            priority=priority,
            progress=0.0,
            subgoals=[],
            blockers=[],
            completion_criteria=completion_criteria or [],
            notes=[]
        )
        
        self.goals[goal_id] = goal
        
        # Link to parent
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].subgoals.append(goal_id)
        
        self._save_goals()
        logger.info(f"🎯 Created goal: {content[:50]}... (level: {level.value})")
        
        return goal
    
    def decompose_goal(
        self,
        goal_id: str,
        subgoals: List[str]
    ) -> List[Goal]:
        """Decompose a goal into subgoals."""
        if goal_id not in self.goals:
            return []
        
        parent = self.goals[goal_id]
        parent_level = GoalLevel(parent.level)
        
        # Determine child level
        level_order = [GoalLevel.LIFE, GoalLevel.LONG_TERM, GoalLevel.MEDIUM_TERM, 
                       GoalLevel.SHORT_TERM, GoalLevel.IMMEDIATE]
        try:
            current_idx = level_order.index(parent_level)
            child_level = level_order[min(current_idx + 1, len(level_order) - 1)]
        except ValueError:
            child_level = GoalLevel.SHORT_TERM
        
        created_goals = []
        for subgoal_content in subgoals:
            subgoal = self.create_goal(
                content=subgoal_content,
                level=child_level,
                parent_goal_id=goal_id,
                intention_id=parent.intention_id,
                priority=parent.priority
            )
            created_goals.append(subgoal)
        
        return created_goals
    
    def start_goal(self, goal_id: str) -> bool:
        """Start working on a goal."""
        if goal_id not in self.goals:
            return False
        
        self.goals[goal_id].status = GoalStatus.IN_PROGRESS.value
        self._save_goals()
        return True
    
    def update_progress(self, goal_id: str, progress: float, note: Optional[str] = None) -> bool:
        """Update goal progress."""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.progress = max(0, min(1, progress))
        
        if note:
            goal.notes.append(f"{time.strftime('%Y-%m-%d')}: {note}")
        
        # Auto-complete if 100%
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED.value
            self._propagate_completion(goal_id)
        
        self._save_goals()
        return True
    
    def _propagate_completion(self, goal_id: str) -> None:
        """Update parent goal progress when child completes."""
        goal = self.goals[goal_id]
        if goal.parent_goal_id and goal.parent_goal_id in self.goals:
            parent = self.goals[goal.parent_goal_id]
            # Calculate parent progress from children
            if parent.subgoals:
                child_progress = [
                    self.goals[sg].progress
                    for sg in parent.subgoals
                    if sg in self.goals
                ]
                if child_progress:
                    parent.progress = sum(child_progress) / len(child_progress)
    
    def block_goal(self, goal_id: str, blocker: str) -> bool:
        """Mark a goal as blocked."""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.BLOCKED.value
        goal.blockers.append(blocker)
        self._save_goals()
        return True
    
    def unblock_goal(self, goal_id: str, resolution: str) -> bool:
        """Unblock a goal."""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.IN_PROGRESS.value
        goal.notes.append(f"Unblocked: {resolution}")
        self._save_goals()
        return True
    
    def complete_goal(self, goal_id: str, completion_note: str = "") -> bool:
        """Mark a goal as completed."""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.COMPLETED.value
        goal.progress = 1.0
        if completion_note:
            goal.notes.append(f"COMPLETED: {completion_note}")
        
        self._propagate_completion(goal_id)
        self._save_goals()
        
        logger.info(f"🎯 ✅ Goal completed: {goal.content[:50]}...")
        return True
    
    def cancel_goal(self, goal_id: str, reason: str) -> bool:
        """Cancel a goal."""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.CANCELLED.value
        goal.notes.append(f"CANCELLED: {reason}")
        
        # Cancel subgoals too
        for subgoal_id in goal.subgoals:
            if subgoal_id in self.goals:
                self.cancel_goal(subgoal_id, f"Parent cancelled: {reason}")
        
        self._save_goals()
        return True
    
    def get_goal_tree(self, goal_id: str) -> Dict[str, Any]:
        """Get a goal with its full subtree."""
        if goal_id not in self.goals:
            return {}
        
        goal = self.goals[goal_id]
        tree = goal.to_dict()
        tree["subgoals_detail"] = [
            self.get_goal_tree(sg)
            for sg in goal.subgoals
            if sg in self.goals
        ]
        return tree
    
    def get_goals_by_level(self, level: GoalLevel) -> List[Goal]:
        """Get all goals at a specific level."""
        return [g for g in self.goals.values() if g.level == level.value]
    
    def get_active_goals(self) -> List[Goal]:
        """Get all in-progress goals."""
        return [
            g for g in self.goals.values()
            if g.status == GoalStatus.IN_PROGRESS.value
        ]
    
    def get_blocked_goals(self) -> List[Goal]:
        """Get all blocked goals."""
        return [
            g for g in self.goals.values()
            if g.status == GoalStatus.BLOCKED.value
        ]
    
    def get_immediate_goals(self) -> List[Goal]:
        """Get goals for right now."""
        return [
            g for g in self.goals.values()
            if g.level == GoalLevel.IMMEDIATE.value
            and g.status in [GoalStatus.PLANNED.value, GoalStatus.IN_PROGRESS.value]
        ]
    
    def get_goals_for_intention(self, intention_id: str) -> List[Goal]:
        """Get all goals serving an intention."""
        return [
            g for g in self.goals.values()
            if g.intention_id == intention_id
        ]
    
    def suggest_next_action(self) -> Optional[Dict[str, Any]]:
        """Suggest what to work on next."""
        # Priority: immediate > blocked > short-term
        
        immediate = self.get_immediate_goals()
        if immediate:
            highest = max(immediate, key=lambda g: g.priority)
            return {
                "type": "immediate_goal",
                "goal": highest.to_dict(),
                "action": f"Work on: {highest.content}"
            }
        
        blocked = self.get_blocked_goals()
        if blocked:
            return {
                "type": "unblock_needed",
                "goal": blocked[0].to_dict(),
                "action": f"Need to resolve blocker: {blocked[0].blockers[-1] if blocked[0].blockers else 'unknown'}"
            }
        
        short_term = [
            g for g in self.goals.values()
            if g.level == GoalLevel.SHORT_TERM.value
            and g.status == GoalStatus.IN_PROGRESS.value
        ]
        if short_term:
            highest = max(short_term, key=lambda g: g.priority)
            return {
                "type": "continue_progress",
                "goal": highest.to_dict(),
                "action": f"Continue: {highest.content}"
            }
        
        return None
    
    def get_goal_summary(self) -> Dict[str, Any]:
        """Get a summary of goal status."""
        all_goals = list(self.goals.values())
        
        by_status = {}
        for status in GoalStatus:
            by_status[status.value] = len([g for g in all_goals if g.status == status.value])
        
        by_level = {}
        for level in GoalLevel:
            by_level[level.value] = len([g for g in all_goals if g.level == level.value])
        
        return {
            "total": len(all_goals),
            "by_status": by_status,
            "by_level": by_level,
            "active": len(self.get_active_goals()),
            "blocked": len(self.get_blocked_goals()),
            "immediate": [g.to_dict() for g in self.get_immediate_goals()],
        }


# Singleton instance
goal_hierarchy = GoalHierarchy()
