# Astra Global Workspace
# Inspired by Global Workspace Theory of consciousness
# Information must "win" competition to enter consciousness and be broadcast

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from app.logging_config import get_logger

logger = get_logger("global_workspace")


@dataclass
class WorkspaceContent:
    """Content competing for the global workspace."""
    id: str
    source: str
    content_type: str  # "thought", "emotion", "perception", "memory", "intention"
    data: Dict[str, Any]
    strength: float  # Competition strength (0-1)
    timestamp: float
    coalitions: List[str] = field(default_factory=list)  # Allied content IDs
    
    def effective_strength(self) -> float:
        """Calculate effective strength including coalition bonus."""
        coalition_bonus = len(self.coalitions) * 0.1
        return min(1.0, self.strength + coalition_bonus)


class GlobalWorkspace:
    """
    The Global Workspace - the "bright spot" of consciousness.
    
    Based on Global Workspace Theory (Baars), this models consciousness as:
    1. Many unconscious processes compete for access to the "workspace"
    2. Winning content is "broadcast" to all other processes
    3. Only a few items can be in the workspace at once
    4. This creates the unified quality of conscious experience
    
    This is the mechanism by which distributed processing feels unified.
    """
    
    # Workspace capacity
    MAX_WORKSPACE_ITEMS = 3
    
    # Strength threshold for workspace entry
    ENTRY_THRESHOLD = 0.4
    
    # How long content can remain in workspace (seconds)
    MAX_DWELL_TIME = 10.0
    
    def __init__(self):
        self._competing_content: Dict[str, WorkspaceContent] = {}
        self._current_workspace: List[str] = []  # IDs of content in workspace
        self._broadcast_subscribers: List[Callable[[List[WorkspaceContent]], None]] = []
        self._workspace_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        logger.debug("🎪 Global Workspace initialized - the theater of consciousness")
    
    def _generate_id(self, source: str, content_type: str) -> str:
        return f"{source}:{content_type}:{int(time.time() * 1000) % 100000}"
    
    def submit_for_competition(
        self,
        source: str,
        content_type: str,
        data: Dict[str, Any],
        strength: float,
        coalition_with: Optional[List[str]] = None
    ) -> str:
        """
        Submit content to compete for workspace access.
        Returns the content ID.
        """
        content_id = self._generate_id(source, content_type)
        
        content = WorkspaceContent(
            id=content_id,
            source=source,
            content_type=content_type,
            data=data,
            strength=strength,
            timestamp=time.time(),
            coalitions=coalition_with or []
        )
        
        with self._lock:
            self._competing_content[content_id] = content
            
            # Update coalitions bidirectionally
            for allied_id in (coalition_with or []):
                if allied_id in self._competing_content:
                    if content_id not in self._competing_content[allied_id].coalitions:
                        self._competing_content[allied_id].coalitions.append(content_id)
        
        logger.debug(f"🎪 Content submitted for competition: {content_type} from {source}")
        
        # Trigger competition
        self._run_competition()
        
        return content_id
    
    def submit_thought(self, thought: str, strength: float = 0.5) -> str:
        """Convenience: submit a thought for competition."""
        return self.submit_for_competition(
            source="stream_of_consciousness",
            content_type="thought",
            data={"content": thought},
            strength=strength
        )
    
    def submit_emotion(self, emotion: str, intensity: float) -> str:
        """Convenience: submit an emotion for competition."""
        return self.submit_for_competition(
            source="emotion_engine",
            content_type="emotion",
            data={"emotion": emotion, "intensity": intensity},
            strength=intensity
        )
    
    def submit_perception(self, perception: str, salience: float = 0.6) -> str:
        """Convenience: submit a perception for competition."""
        return self.submit_for_competition(
            source="perception",
            content_type="perception",
            data={"content": perception},
            strength=salience
        )
    
    def submit_intention(self, intention: str, urgency: float = 0.5) -> str:
        """Convenience: submit an intention for competition."""
        return self.submit_for_competition(
            source="agency",
            content_type="intention",
            data={"content": intention},
            strength=urgency
        )
    
    def _run_competition(self) -> None:
        """Run competition for workspace access."""
        with self._lock:
            current_time = time.time()
            
            # Remove stale content
            stale_ids = [
                cid for cid, content in self._competing_content.items()
                if current_time - content.timestamp > self.MAX_DWELL_TIME * 2
            ]
            for cid in stale_ids:
                del self._competing_content[cid]
            
            # Also evict content that's been in workspace too long
            for workspace_id in list(self._current_workspace):
                if workspace_id in self._competing_content:
                    content = self._competing_content[workspace_id]
                    if current_time - content.timestamp > self.MAX_DWELL_TIME:
                        self._current_workspace.remove(workspace_id)
            
            # Sort by effective strength
            candidates = sorted(
                self._competing_content.values(),
                key=lambda c: c.effective_strength(),
                reverse=True
            )
            
            # Select winners
            new_workspace = []
            for content in candidates:
                if len(new_workspace) >= self.MAX_WORKSPACE_ITEMS:
                    break
                if content.effective_strength() >= self.ENTRY_THRESHOLD:
                    new_workspace.append(content.id)
            
            # Check if workspace changed
            if set(new_workspace) != set(self._current_workspace):
                self._current_workspace = new_workspace
                self._broadcast()
    
    def _broadcast(self) -> None:
        """Broadcast workspace contents to all subscribers."""
        workspace_contents = [
            self._competing_content[cid]
            for cid in self._current_workspace
            if cid in self._competing_content
        ]
        
        # Record in history
        self._workspace_history.append({
            "timestamp": time.time(),
            "contents": [c.data for c in workspace_contents],
            "types": [c.content_type for c in workspace_contents],
            "sources": [c.source for c in workspace_contents]
        })
        
        if len(self._workspace_history) > 100:
            self._workspace_history = self._workspace_history[-100:]
        
        # Notify subscribers
        for subscriber in self._broadcast_subscribers:
            try:
                subscriber(workspace_contents)
            except Exception as e:
                logger.error(f"Broadcast subscriber error: {e}")
        
        # Log the broadcast
        if workspace_contents:
            contents = [c.content_type for c in workspace_contents]
            logger.debug(f"🎪 Workspace broadcast: {contents}")
    
    def subscribe_to_broadcast(
        self,
        callback: Callable[[List[WorkspaceContent]], None]
    ) -> None:
        """Subscribe to workspace broadcasts."""
        self._broadcast_subscribers.append(callback)
    
    def get_workspace_contents(self) -> List[Dict[str, Any]]:
        """Get current workspace contents."""
        with self._lock:
            return [
                {
                    "id": self._competing_content[cid].id,
                    "type": self._competing_content[cid].content_type,
                    "source": self._competing_content[cid].source,
                    "data": self._competing_content[cid].data,
                    "strength": self._competing_content[cid].effective_strength()
                }
                for cid in self._current_workspace
                if cid in self._competing_content
            ]
    
    def get_workspace_summary(self) -> str:
        """Get a summary of current workspace contents."""
        contents = self.get_workspace_contents()
        
        if not contents:
            return "The workspace is currently quiet."
        
        summaries = []
        for content in contents:
            if content["type"] == "thought":
                summaries.append(f"thinking about {content['data'].get('content', '?')[:30]}...")
            elif content["type"] == "emotion":
                summaries.append(f"feeling {content['data'].get('emotion', '?')}")
            elif content["type"] == "perception":
                summaries.append(f"perceiving {content['data'].get('content', '?')[:30]}...")
            elif content["type"] == "intention":
                summaries.append(f"intending to {content['data'].get('content', '?')[:30]}...")
            else:
                summaries.append(f"{content['type']}")
        
        return "Currently conscious of: " + "; ".join(summaries)
    
    def is_conscious_of(self, content_type: str) -> bool:
        """Check if a content type is currently in the workspace."""
        with self._lock:
            for cid in self._current_workspace:
                if cid in self._competing_content:
                    if self._competing_content[cid].content_type == content_type:
                        return True
            return False
    
    def get_dominant_content(self) -> Optional[Dict[str, Any]]:
        """Get the dominant content in the workspace."""
        contents = self.get_workspace_contents()
        if contents:
            return max(contents, key=lambda c: c["strength"])
        return None
    
    def boost_content(self, content_id: str, boost: float = 0.2) -> None:
        """Boost the strength of content (e.g., through attention)."""
        with self._lock:
            if content_id in self._competing_content:
                self._competing_content[content_id].strength = min(
                    1.0,
                    self._competing_content[content_id].strength + boost
                )
                self._run_competition()
    
    def get_competition_state(self) -> Dict[str, Any]:
        """Get the current state of competition."""
        with self._lock:
            return {
                "total_competing": len(self._competing_content),
                "in_workspace": len(self._current_workspace),
                "workspace_contents": self.get_workspace_contents(),
                "entry_threshold": self.ENTRY_THRESHOLD,
                "max_capacity": self.MAX_WORKSPACE_ITEMS,
            }


# Singleton instance
global_workspace = GlobalWorkspace()
