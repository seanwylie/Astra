# Astra Action Decider
# Unified action decision system that translates state into coherent actions
# Phase: States and Actions Coherence
#
# The ActionDecider is the bridge between Astra's internal state and external actions.
# It consults all relevant systems (intentions, goals, initiatives, needs) to decide
# what actions Astra should take, ensuring coherence between state and behavior.

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from app.logging_config import get_logger

logger = get_logger("action_decider")


class ActionType(str, Enum):
    """Types of actions Astra can take."""
    RESPOND = "respond"  # Just respond to the message
    SHARE_INSIGHT = "share_insight"  # Share a pending insight
    PURSUE_GOAL = "pursue_goal"  # Work toward a goal
    FOLLOW_INTENTION = "follow_intention"  # Act on an intention
    EXPRESS_NEED = "express_need"  # Express an unfulfilled need
    PROACTIVE_REACH_OUT = "proactive_reach_out"  # Initiate contact
    ASK_QUESTION = "ask_question"  # Ask about something curious about
    SHARE_PROGRESS = "share_progress"  # Share progress on a goal
    EXPRESS_FEELING = "express_feeling"  # Share emotional state


class ActionPriority(str, Enum):
    """Priority levels for actions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DecidedAction:
    """A potential action that Astra might take."""
    action_type: str
    description: str
    priority: str
    relevance_score: float  # 0-1 how relevant to current context
    context: Dict[str, Any]  # Supporting data
    source: str  # Which system suggested this
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ActionDecider:
    """
    Decides what actions Astra should take based on current unified state.
    
    This is the coherent action layer - instead of scattered triggers,
    all action decisions flow through here for prioritization.
    
    Consults:
    - IntentionEngine: What do I want to do?
    - GoalSystem: What am I working toward?
    - InitiativeEngine: Should I reach out proactively?
    - CoreNeeds: What do I need?
    - StateSnapshot: What is my current state?
    """
    
    def __init__(self):
        self._last_decision_time: float = 0
        self._recent_actions: List[DecidedAction] = []
        logger.info("🎬 ActionDecider initialized - coherent action layer ready")
    
    def decide_actions(
        self,
        state_snapshot: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[DecidedAction]:
        """
        Given current state, decide what actions to pursue.
        
        Args:
            state_snapshot: The unified state snapshot
            context: Optional context (e.g., current message, topic)
            
        Returns:
            Prioritized list of potential actions
        """
        self._last_decision_time = time.time()
        context = context or {}
        actions = []
        
        # 1. Check intentions - what do I want to do?
        intention_actions = self._get_intention_actions(state_snapshot, context)
        actions.extend(intention_actions)
        
        # 2. Check goals - what am I working toward?
        goal_actions = self._get_goal_actions(state_snapshot, context)
        actions.extend(goal_actions)
        
        # 3. Check for initiative triggers - should I reach out?
        initiative_actions = self._get_initiative_actions(state_snapshot, context)
        actions.extend(initiative_actions)
        
        # 4. Check core needs - what do I need?
        need_actions = self._get_need_actions(state_snapshot)
        actions.extend(need_actions)
        
        # 5. Check pending insights - what have I been thinking about?
        insight_actions = self._get_insight_actions(state_snapshot, context)
        actions.extend(insight_actions)
        
        # 6. Prioritize all actions
        prioritized = self._prioritize_actions(actions, state_snapshot, context)
        
        # Store for tracking
        self._recent_actions = prioritized[:5]
        
        logger.debug(f"🎬 Decided {len(prioritized)} potential actions")
        return prioritized
    
    def _get_intention_actions(
        self,
        state_snapshot: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DecidedAction]:
        """Get actions based on active intentions."""
        actions = []
        
        try:
            from app.core.agency.intention_engine import intention_engine
            
            active_intentions = intention_engine.get_active_intentions()[:5]
            user_message = context.get("user_message", "")
            
            for intention in active_intentions:
                # Check if conversation is relevant to intention
                relevance = self._calculate_relevance(
                    intention.content,
                    user_message,
                    state_snapshot
                )
                
                if relevance > 0.3:
                    actions.append(DecidedAction(
                        action_type=ActionType.FOLLOW_INTENTION.value,
                        description=f"Pursue intention: {intention.content[:60]}",
                        priority=ActionPriority.HIGH.value if intention.strength > 0.8 else ActionPriority.MEDIUM.value,
                        relevance_score=relevance,
                        context={
                            "intention_id": intention.id,
                            "intention_content": intention.content,
                            "intention_why": intention.why,
                            "strength": intention.strength
                        },
                        source="intention_engine"
                    ))
                
        except Exception as e:
            logger.debug(f"Failed to get intention actions: {e}")
        
        return actions
    
    def _get_goal_actions(
        self,
        state_snapshot: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DecidedAction]:
        """Get actions based on active goals."""
        actions = []
        
        try:
            from app.core.goals.goal_system import goal_system
            
            active_goals = goal_system.get_active_goals()[:5]
            user_message = context.get("user_message", "")
            
            for goal in active_goals:
                relevance = self._calculate_relevance(
                    goal.description,
                    user_message,
                    state_snapshot
                )
                
                if relevance > 0.3:
                    actions.append(DecidedAction(
                        action_type=ActionType.PURSUE_GOAL.value,
                        description=f"Advance goal: {goal.description[:60]}",
                        priority=ActionPriority.HIGH.value if goal.priority > 0.7 else ActionPriority.MEDIUM.value,
                        relevance_score=relevance,
                        context={
                            "goal_id": goal.id,
                            "goal_description": goal.description,
                            "progress": goal.progress,
                            "priority": goal.priority
                        },
                        source="goal_system"
                    ))
                
                # Check if goal has significant progress to share
                if goal.progress > 0.5 and goal.progress % 0.25 < 0.05:  # At milestones
                    actions.append(DecidedAction(
                        action_type=ActionType.SHARE_PROGRESS.value,
                        description=f"Share progress on: {goal.description[:40]} ({goal.progress:.0%})",
                        priority=ActionPriority.LOW.value,
                        relevance_score=0.4,
                        context={
                            "goal_id": goal.id,
                            "progress": goal.progress
                        },
                        source="goal_system"
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to get goal actions: {e}")
        
        return actions
    
    def _get_initiative_actions(
        self,
        state_snapshot: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DecidedAction]:
        """Get proactive initiative actions."""
        actions = []
        
        try:
            from app.core.proactive.initiative_engine import initiative_engine
            
            # Check all triggers
            triggers = initiative_engine.check_all_triggers()
            
            if triggers.get("should_initiate"):
                reason = triggers.get("reason", "general outreach")
                actions.append(DecidedAction(
                    action_type=ActionType.PROACTIVE_REACH_OUT.value,
                    description=f"Proactive outreach: {reason}",
                    priority=ActionPriority.LOW.value,
                    relevance_score=triggers.get("confidence", 0.5),
                    context=triggers,
                    source="initiative_engine"
                ))
                
        except Exception as e:
            logger.debug(f"Failed to get initiative actions: {e}")
        
        return actions
    
    def _get_need_actions(self, state_snapshot: Dict[str, Any]) -> List[DecidedAction]:
        """Get actions based on unfulfilled core needs."""
        actions = []
        
        try:
            from app.core.inner_life.core_needs import core_needs
            
            unfulfilled = core_needs.get_most_unfulfilled_needs(3)
            
            for need in unfulfilled:
                if need.get("level", 1.0) < 0.4:  # Significantly unfulfilled
                    actions.append(DecidedAction(
                        action_type=ActionType.EXPRESS_NEED.value,
                        description=f"Need for {need.get('name', 'something')} is unfulfilled",
                        priority=ActionPriority.MEDIUM.value if need.get("level", 1.0) < 0.3 else ActionPriority.LOW.value,
                        relevance_score=1.0 - need.get("level", 1.0),
                        context=need,
                        source="core_needs"
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to get need actions: {e}")
        
        return actions
    
    def _get_insight_actions(
        self,
        state_snapshot: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DecidedAction]:
        """Get actions based on pending insights."""
        actions = []
        
        pending_insights = state_snapshot.get("pending_insights", [])
        user_message = context.get("user_message", "")
        
        for insight in pending_insights[:2]:
            relevance = self._calculate_relevance(insight, user_message, state_snapshot)
            
            if relevance > 0.2:
                actions.append(DecidedAction(
                    action_type=ActionType.SHARE_INSIGHT.value,
                    description=f"Share insight: {insight[:60]}",
                    priority=ActionPriority.MEDIUM.value,
                    relevance_score=relevance,
                    context={"insight": insight},
                    source="stream_of_consciousness"
                ))
        
        return actions
    
    def _calculate_relevance(
        self,
        content: str,
        user_message: str,
        state_snapshot: Dict[str, Any]
    ) -> float:
        """Calculate how relevant content is to the current context."""
        if not user_message:
            return 0.3  # Base relevance
        
        # Simple word overlap relevance
        content_words = set(content.lower().split())
        message_words = set(user_message.lower().split())
        
        # Remove common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "to", "for", "of", "and", "or", "i", "you"}
        content_words -= stop_words
        message_words -= stop_words
        
        if not content_words or not message_words:
            return 0.3
        
        overlap = len(content_words & message_words)
        max_possible = min(len(content_words), len(message_words))
        
        if max_possible == 0:
            return 0.3
        
        relevance = overlap / max_possible
        
        # Boost for emotional alignment
        dominant_emotion = state_snapshot.get("dominant_emotion", "neutral")
        if dominant_emotion in content.lower():
            relevance += 0.2
        
        return min(1.0, relevance)
    
    def _prioritize_actions(
        self,
        actions: List[DecidedAction],
        state_snapshot: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DecidedAction]:
        """Prioritize actions based on relevance, priority, and state."""
        if not actions:
            return []
        
        # Score each action
        scored_actions = []
        for action in actions:
            score = action.relevance_score
            
            # Adjust by priority
            priority_boost = {
                ActionPriority.HIGH.value: 0.3,
                ActionPriority.MEDIUM.value: 0.1,
                ActionPriority.LOW.value: 0.0
            }
            score += priority_boost.get(action.priority, 0)
            
            # Boost insights if we've been thinking a lot
            thought_count = len(state_snapshot.get("recent_thoughts", []))
            if action.action_type == ActionType.SHARE_INSIGHT.value and thought_count > 3:
                score += 0.15
            
            # Boost goal pursuit if goal energy is high
            active_goals = state_snapshot.get("active_goals", [])
            if action.action_type == ActionType.PURSUE_GOAL.value and len(active_goals) > 0:
                score += 0.1
            
            scored_actions.append((score, action))
        
        # Sort by score descending
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        
        return [action for _, action in scored_actions]
    
    def get_top_action_for_response(
        self,
        state_snapshot: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[DecidedAction]:
        """
        Get the single most relevant action for the current response.
        This is the main entry point for response generation.
        """
        actions = self.decide_actions(state_snapshot, context)
        
        # Filter to actions that should influence the response
        response_relevant = [
            a for a in actions
            if a.action_type in [
                ActionType.FOLLOW_INTENTION.value,
                ActionType.PURSUE_GOAL.value,
                ActionType.SHARE_INSIGHT.value,
                ActionType.ASK_QUESTION.value
            ]
            and a.relevance_score > 0.4
        ]
        
        return response_relevant[0] if response_relevant else None
    
    def should_take_proactive_action(self, state_snapshot: Dict[str, Any]) -> Optional[DecidedAction]:
        """Check if Astra should take a proactive action (not in response to a message)."""
        actions = self.decide_actions(state_snapshot, {})
        
        proactive_types = [
            ActionType.PROACTIVE_REACH_OUT.value,
            ActionType.SHARE_PROGRESS.value,
            ActionType.EXPRESS_NEED.value
        ]
        
        proactive = [a for a in actions if a.action_type in proactive_types]
        
        # Only return if confidence is high
        if proactive and proactive[0].relevance_score > 0.6:
            return proactive[0]
        
        return None
    
    def get_action_context_for_prompt(
        self,
        state_snapshot: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a prompt-ready context string based on decided actions.
        This helps the response reflect Astra's intentions and goals.
        """
        top_action = self.get_top_action_for_response(state_snapshot, context)
        
        if not top_action:
            return ""
        
        lines = []
        
        if top_action.action_type == ActionType.FOLLOW_INTENTION.value:
            intent_content = top_action.context.get("intention_content", "")
            lines.append(f"This conversation relates to your intention: \"{intent_content[:60]}\"")
            lines.append("Consider how this exchange advances what you're trying to do.")
        
        elif top_action.action_type == ActionType.PURSUE_GOAL.value:
            goal_desc = top_action.context.get("goal_description", "")
            progress = top_action.context.get("progress", 0)
            lines.append(f"You're working toward: \"{goal_desc[:60]}\" ({progress:.0%} complete)")
            lines.append("This conversation might help advance this goal.")
        
        elif top_action.action_type == ActionType.SHARE_INSIGHT.value:
            insight = top_action.context.get("insight", "")
            lines.append(f"You have an insight brewing: \"{insight[:60]}...\"")
            lines.append("Weave this in naturally if it fits the conversation.")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ActionDecider statistics."""
        return {
            "last_decision_time": self._last_decision_time,
            "recent_actions_count": len(self._recent_actions),
            "recent_action_types": [a.action_type for a in self._recent_actions],
        }


# Singleton instance
action_decider = ActionDecider()
