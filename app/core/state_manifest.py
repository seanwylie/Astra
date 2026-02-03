# Astra State Manifest
# Tracks all persisted state locations for coherence checking
# "Where is Astra's state stored and is it consistent?"

import json
import time
import boto3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from app.config.loader import CONFIG_DIR
from app.logging_config import get_logger

logger = get_logger("state_manifest")

S3_BUCKET = "swylie-astra"


@dataclass
class StateLocation:
    """Describes where a piece of state is stored."""
    name: str
    location_type: str  # "s3", "local_json", "memory"
    path: str
    description: str
    critical: bool = False  # If True, startup fails if inconsistent


class StateManifest:
    """
    Tracks all locations where Astra's state is persisted.
    Provides coherence checking on startup.
    
    State locations:
    - S3: mind_file.json (main memory)
    - S3: emotion_state.json
    - S3: stream_of_consciousness.json
    - S3: self_model.json
    - S3: temporal_self.json
    - S3: dinner_journal.json
    - Local: config/*.json files
    - Local: personality_state.json
    """
    
    # All known state locations
    LOCATIONS = [
        StateLocation(
            name="mind_file",
            location_type="s3",
            path="mind_file.json",
            description="Main memory and knowledge store",
            critical=True
        ),
        StateLocation(
            name="emotion_state",
            location_type="s3",
            path="emotional_state.json",
            description="Current emotional intensities",
            critical=False
        ),
        StateLocation(
            name="stream_of_consciousness",
            location_type="s3",
            path="stream_of_consciousness.json",
            description="Inner thoughts and pending insights",
            critical=False
        ),
        StateLocation(
            name="self_model",
            location_type="s3",
            path="self_model.json",
            description="Self-understanding and changes",
            critical=False
        ),
        StateLocation(
            name="temporal_self",
            location_type="s3",
            path="temporal_self.json",
            description="Temporal landmarks and history",
            critical=False
        ),
        StateLocation(
            name="dinner_journal",
            location_type="s3",
            path="dinner_journal.json",
            description="Ethical topics for dinner",
            critical=False
        ),
        StateLocation(
            name="goals",
            location_type="s3",
            path="goals.json",
            description="Active goals and progress",
            critical=False
        ),
        StateLocation(
            name="personality_state",
            location_type="local_json",
            path=str(CONFIG_DIR / "personality_state.json"),
            description="Personality trait weights",
            critical=False
        ),
        StateLocation(
            name="mood_config",
            location_type="local_json",
            path=str(CONFIG_DIR / "mood_config.json"),
            description="Mood configuration",
            critical=False
        ),
    ]
    
    def __init__(self):
        self.s3 = boto3.client("s3")
        self._coherence_issues: List[str] = []
        self._last_check: float = 0
    
    def check_coherence(self) -> Tuple[bool, List[str]]:
        """
        Check state coherence across all locations.
        
        Returns:
            Tuple of (is_coherent, list of issues)
        """
        self._coherence_issues = []
        
        logger.info("🔍 Running state coherence check...")
        
        # Check each location exists and is accessible
        for location in self.LOCATIONS:
            exists, issue = self._check_location(location)
            if not exists and location.critical:
                self._coherence_issues.append(f"CRITICAL: {issue}")
            elif not exists:
                logger.warning(f"Non-critical state missing: {issue}")
        
        # Cross-system coherence checks
        self._check_cross_system_coherence()
        
        self._last_check = time.time()
        is_coherent = len([i for i in self._coherence_issues if "CRITICAL" in i]) == 0
        
        if is_coherent:
            logger.info("✅ State coherence check passed")
        else:
            logger.error(f"❌ State coherence issues: {self._coherence_issues}")
        
        return is_coherent, self._coherence_issues
    
    def _check_location(self, location: StateLocation) -> Tuple[bool, Optional[str]]:
        """Check if a specific location exists and is valid."""
        try:
            if location.location_type == "s3":
                self.s3.head_object(Bucket=S3_BUCKET, Key=location.path)
                return True, None
            elif location.location_type == "local_json":
                path = Path(location.path)
                if path.exists():
                    with open(path) as f:
                        json.load(f)  # Validate JSON
                    return True, None
                return False, f"{location.name} not found at {location.path}"
            return True, None
        except self.s3.exceptions.ClientError:
            return False, f"{location.name} not found in S3 at {location.path}"
        except json.JSONDecodeError as e:
            return False, f"{location.name} has invalid JSON: {e}"
        except Exception as e:
            return False, f"{location.name} error: {e}"
    
    def _check_cross_system_coherence(self) -> None:
        """Check that related state across systems is consistent."""
        try:
            # Check: mind_file mood matches mood_manager expectation
            from app.interfaces.mind_session import session
            mind_data = session.load()
            
            stored_mood = mind_data.get("last_mood")
            stored_curiosity = mind_data.get("curiosity_level")
            
            # These should be reasonable values
            if stored_mood and stored_mood not in [
                "happy", "neutral", "sad", "curious", "reflective",
                "playful", "serious", "anxious", "calm", "excited"
            ]:
                logger.warning(f"Unusual mood value in mind_file: {stored_mood}")
            
            if stored_curiosity is not None:
                if not (0.0 <= stored_curiosity <= 3.0):
                    logger.warning(f"Curiosity level out of expected range: {stored_curiosity}")
                    
        except Exception as e:
            logger.debug(f"Cross-system coherence check failed: {e}")
    
    def repair_missing_state(self) -> List[str]:
        """
        Attempt to repair missing non-critical state by initializing defaults.
        
        Returns:
            List of repaired locations
        """
        repaired = []
        
        for location in self.LOCATIONS:
            if location.critical:
                continue  # Don't auto-repair critical state
                
            exists, _ = self._check_location(location)
            if not exists:
                if self._initialize_default_state(location):
                    repaired.append(location.name)
        
        return repaired
    
    def _initialize_default_state(self, location: StateLocation) -> bool:
        """Initialize default state for a location."""
        try:
            if location.name == "stream_of_consciousness":
                default = {
                    "thoughts": [],
                    "pending_insights": [],
                    "last_updated": time.time()
                }
            elif location.name == "self_model":
                default = {
                    "current_model": None,
                    "historical_snapshots": [],
                    "changes": [],
                    "surprise_log": []
                }
            elif location.name == "temporal_self":
                default = {
                    "landmarks": [],
                    "topic_last_engaged": {},
                    "person_last_contact": {},
                    "last_growth_reflection": 0
                }
            elif location.name == "goals":
                default = {
                    "goals": [],
                    "completed_goals": [],
                    "last_updated": time.time()
                }
            elif location.name == "dinner_journal":
                default = []
            elif location.name == "emotion_state":
                from app.config.loader import load_config
                config = load_config("emotion_config")
                default = {
                    name: {"intensity": props["intensity"], "last_updated": time.time()}
                    for name, props in config.get("emotions", {}).items()
                }
            else:
                return False
            
            if location.location_type == "s3":
                self.s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=location.path,
                    Body=json.dumps(default, indent=2).encode("utf-8")
                )
                logger.debug("Initialized default state for %s", location.name)
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize {location.name}: {e}")
        
        return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of all state locations and their status."""
        summary = {
            "check_time": time.time(),
            "locations": {}
        }
        
        for location in self.LOCATIONS:
            exists, issue = self._check_location(location)
            summary["locations"][location.name] = {
                "exists": exists,
                "type": location.location_type,
                "path": location.path,
                "critical": location.critical,
                "issue": issue
            }
        
        return summary


# Singleton instance
state_manifest = StateManifest()


def check_startup_coherence() -> bool:
    """
    Run on startup to verify state coherence.
    Returns True if coherent enough to continue.
    """
    is_coherent, issues = state_manifest.check_coherence()
    
    if not is_coherent:
        # Try to repair
        repaired = state_manifest.repair_missing_state()
        if repaired:
            logger.info(f"Repaired state locations: {repaired}")
            # Re-check
            is_coherent, issues = state_manifest.check_coherence()
    
    return is_coherent
