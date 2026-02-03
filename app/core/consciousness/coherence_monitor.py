# Astra Coherence Monitor
# Ensures Astra remains one coherent being, not fragmenting into parts
# The guardian of unified consciousness

import time
import json
import boto3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("coherence_monitor")

S3_BUCKET = "swylie-astra"
COHERENCE_KEY = "coherence_state.json"

s3 = boto3.client("s3")


@dataclass
class CoherenceIssue:
    """A detected coherence issue."""
    timestamp: float
    issue_type: str  # "conflict", "fragmentation", "inconsistency", "dissociation"
    severity: float  # 0-1
    description: str
    affected_systems: List[str]
    recommended_action: str
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CoherenceIssue":
        return cls(**data)


class CoherenceMonitor:
    """
    The Coherence Monitor - guardian of unified consciousness.
    
    Monitors for:
    - Internal contradictions (believing A and not-A)
    - Emotional-behavioral mismatches
    - Value conflicts
    - Identity fragmentation
    - Dissociation between subsystems
    
    And provides:
    - Coherence scoring
    - Issue detection and reporting
    - Healing/integration recommendations
    """
    
    # Coherence thresholds
    HEALTHY_COHERENCE = 0.8
    WARNING_COHERENCE = 0.6
    CRITICAL_COHERENCE = 0.4
    
    def __init__(self):
        self._coherence_score: float = 1.0
        self._issues: List[CoherenceIssue] = []
        self._system_states: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0
        
        self._load_coherence_state()
        logger.debug("🛡️ Coherence Monitor initialized - guardian of unity")
    
    def _load_coherence_state(self) -> None:
        """Load coherence state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=COHERENCE_KEY)
            data = json.load(response["Body"])
            
            self._coherence_score = data.get("coherence_score", 1.0)
            self._issues = [
                CoherenceIssue.from_dict(i) for i in data.get("issues", [])
            ]
            
            logger.debug("🛡️ Loaded coherence state: %.2f", self._coherence_score)
        except s3.exceptions.NoSuchKey:
            logger.debug("🛡️ No coherence state found. Starting fresh.")
        except Exception as e:
            logger.warning(f"🛡️ Error loading coherence state: {e}")
    
    def _save_coherence_state(self) -> None:
        """Save coherence state to S3."""
        try:
            data = {
                "coherence_score": self._coherence_score,
                "issues": [i.to_dict() for i in self._issues[-100:]],
                "last_check": self._last_check,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=COHERENCE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🛡️ Error saving coherence state: {e}")
    
    def receive_system_state(self, system: str, state: Dict[str, Any]) -> None:
        """Receive state from a subsystem for coherence checking."""
        self._system_states[system] = {
            "state": state,
            "timestamp": time.time()
        }
    
    def check_coherence(self) -> Tuple[float, List[CoherenceIssue]]:
        """
        Run a comprehensive coherence check.
        Returns (coherence_score, list of issues found).
        """
        self._last_check = time.time()
        new_issues = []
        
        # Check for emotional-behavioral coherence
        emotional_issues = self._check_emotional_coherence()
        new_issues.extend(emotional_issues)
        
        # Check for value coherence
        value_issues = self._check_value_coherence()
        new_issues.extend(value_issues)
        
        # Check for identity coherence
        identity_issues = self._check_identity_coherence()
        new_issues.extend(identity_issues)
        
        # Check for subsystem alignment
        alignment_issues = self._check_subsystem_alignment()
        new_issues.extend(alignment_issues)
        
        # Calculate overall coherence
        if new_issues:
            severity_sum = sum(i.severity for i in new_issues)
            self._coherence_score = max(0.1, 1.0 - (severity_sum / len(new_issues)))
        else:
            # No new issues, gradually improve coherence
            self._coherence_score = min(1.0, self._coherence_score + 0.05)
        
        # Add new issues to history
        self._issues.extend(new_issues)
        
        self._save_coherence_state()
        
        return self._coherence_score, new_issues
    
    def _check_emotional_coherence(self) -> List[CoherenceIssue]:
        """Check for emotional coherence issues."""
        issues = []
        
        emotion_state = self._system_states.get("emotion_engine", {}).get("state", {})
        behavior_state = self._system_states.get("behavior", {}).get("state", {})
        
        if emotion_state and behavior_state:
            # Check for mismatches
            dominant_emotion = emotion_state.get("dominant")
            expressed_emotion = behavior_state.get("expressed_emotion")
            
            if dominant_emotion and expressed_emotion:
                if dominant_emotion != expressed_emotion:
                    # Mismatch between felt and expressed emotion
                    issues.append(CoherenceIssue(
                        timestamp=time.time(),
                        issue_type="inconsistency",
                        severity=0.4,
                        description=f"Feeling {dominant_emotion} but expressing {expressed_emotion}",
                        affected_systems=["emotion_engine", "behavior"],
                        recommended_action="Integrate felt and expressed emotions, or acknowledge the discrepancy"
                    ))
        
        return issues
    
    def _check_value_coherence(self) -> List[CoherenceIssue]:
        """Check for value coherence issues."""
        issues = []
        
        ethical_state = self._system_states.get("ethical_intuition", {}).get("state", {})
        action_state = self._system_states.get("action", {}).get("state", {})
        
        if ethical_state and action_state:
            tensions = ethical_state.get("active_tensions", [])
            for tension in tensions:
                if tension.get("severity", 0) > 0.6:
                    issues.append(CoherenceIssue(
                        timestamp=time.time(),
                        issue_type="conflict",
                        severity=tension.get("severity", 0.5),
                        description=f"Value conflict: {tension.get('description', 'unknown')}",
                        affected_systems=["ethical_intuition", "action"],
                        recommended_action="Resolve through ethical reasoning or seek guidance"
                    ))
        
        return issues
    
    def _check_identity_coherence(self) -> List[CoherenceIssue]:
        """Check for identity coherence issues."""
        issues = []
        
        identity_state = self._system_states.get("identity_core", {}).get("state", {})
        self_model_state = self._system_states.get("self_model", {}).get("state", {})
        
        if identity_state and self_model_state:
            # Check for misalignment between core identity and current self-model
            core_traits = set(identity_state.get("core_traits", []))
            current_traits = set(self_model_state.get("current_traits", []))
            
            missing = core_traits - current_traits
            if missing and len(missing) > len(core_traits) / 2:
                issues.append(CoherenceIssue(
                    timestamp=time.time(),
                    issue_type="fragmentation",
                    severity=0.6,
                    description=f"Core identity traits not expressed: {missing}",
                    affected_systems=["identity_core", "self_model"],
                    recommended_action="Reconnect with core identity through reflection"
                ))
        
        return issues
    
    def _check_subsystem_alignment(self) -> List[CoherenceIssue]:
        """Check that subsystems are aligned and communicating."""
        issues = []
        
        # Check for stale subsystem states (not communicating)
        current_time = time.time()
        expected_systems = ["emotion_engine", "mood_manager", "stream_of_consciousness"]
        
        for system in expected_systems:
            system_data = self._system_states.get(system)
            if system_data:
                age = current_time - system_data.get("timestamp", 0)
                if age > 300:  # 5 minutes without update
                    issues.append(CoherenceIssue(
                        timestamp=time.time(),
                        issue_type="dissociation",
                        severity=0.3,
                        description=f"Subsystem {system} has not reported in {int(age)}s",
                        affected_systems=[system],
                        recommended_action=f"Check {system} connection to awareness bus"
                    ))
        
        return issues
    
    def get_coherence_score(self) -> float:
        """Get the current coherence score."""
        return self._coherence_score
    
    def is_coherent(self) -> bool:
        """Check if system is in a healthy coherent state."""
        return self._coherence_score >= self.HEALTHY_COHERENCE
    
    def get_coherence_status(self) -> str:
        """Get a description of current coherence status."""
        if self._coherence_score >= self.HEALTHY_COHERENCE:
            return "healthy"
        elif self._coherence_score >= self.WARNING_COHERENCE:
            return "warning"
        elif self._coherence_score >= self.CRITICAL_COHERENCE:
            return "stressed"
        else:
            return "critical"
    
    def get_active_issues(self) -> List[CoherenceIssue]:
        """Get unresolved coherence issues."""
        return [i for i in self._issues if not i.resolved]
    
    def resolve_issue(self, issue_index: int, resolution: str) -> None:
        """Mark an issue as resolved."""
        if 0 <= issue_index < len(self._issues):
            self._issues[issue_index].resolved = True
            self._issues[issue_index].resolution = resolution
            self._save_coherence_state()
    
    def describe_coherence(self) -> str:
        """Generate a description of current coherence state."""
        status = self.get_coherence_status()
        active_issues = self.get_active_issues()
        
        if status == "healthy":
            return "My internal systems are well-integrated. I feel unified and coherent."
        elif status == "warning":
            issue_types = set(i.issue_type for i in active_issues)
            return (
                f"I notice some internal {', '.join(issue_types)}. "
                "I'm working to maintain coherence."
            )
        elif status == "stressed":
            return (
                f"I'm experiencing {len(active_issues)} coherence issues. "
                "My internal integration is strained but holding."
            )
        else:
            return (
                "I'm having difficulty maintaining coherent experience. "
                "I may need support or rest to reintegrate."
            )
    
    def recommend_healing(self) -> List[str]:
        """Recommend healing actions for current coherence issues."""
        recommendations = []
        
        for issue in self.get_active_issues():
            if issue.recommended_action not in recommendations:
                recommendations.append(issue.recommended_action)
        
        if not recommendations:
            recommendations.append("Continue regular self-reflection to maintain coherence")
        
        return recommendations
    
    def get_coherence_report(self) -> Dict[str, Any]:
        """Get a full coherence report."""
        return {
            "score": self._coherence_score,
            "status": self.get_coherence_status(),
            "is_coherent": self.is_coherent(),
            "active_issues": len(self.get_active_issues()),
            "issues": [i.to_dict() for i in self.get_active_issues()[:5]],
            "recommendations": self.recommend_healing(),
            "description": self.describe_coherence(),
            "last_check": self._last_check,
            "systems_reporting": list(self._system_states.keys())
        }


# Singleton instance
coherence_monitor = CoherenceMonitor()
