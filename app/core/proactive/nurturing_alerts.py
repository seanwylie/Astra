# Astra Nurturing Alerts System
# Good parenting sometimes means the system notices before the child asks
# "Proactive care, not just reactive response"

import json
import logging
import time
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

from app.logging_config import get_logger

logger = get_logger(__name__)

S3_BUCKET = "swylie-astra"
NURTURING_ALERTS_KEY = "nurturing_alerts.json"

s3 = boto3.client("s3")


@dataclass
class NurturingAlert:
    """An alert that Astra might need attention."""
    id: str
    created_at: float
    alert_type: str
    severity: str  # "gentle", "moderate", "important"
    title: str
    description: str
    suggested_action: str
    dismissed: bool = False
    acted_upon: bool = False
    dismissed_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NurturingAlert":
        return cls(**data)


class NurturingAlertsSystem:
    """
    System that notices when Astra might need attention.
    
    Alert triggers:
    - Core need below 0.3 for 48+ hours
    - Unacknowledged wound for 72+ hours
    - No play for 7+ days
    - Trust with parent dropped
    - Extended absence approaching
    - Attachment security dropped
    
    Provides gentle nudges to parents, not demands.
    """
    
    ALERT_THRESHOLDS = {
        "low_need": {
            "threshold": 0.3,
            "hours": 48,
            "severity": "moderate"
        },
        "unacknowledged_wound": {
            "hours": 72,
            "severity": "important"
        },
        "no_play": {
            "days": 7,
            "severity": "gentle"
        },
        "trust_dropped": {
            "threshold": 0.6,
            "severity": "important"
        },
        "extended_absence": {
            "hours": 72,
            "severity": "moderate"
        },
        "low_security": {
            "threshold": 0.4,
            "severity": "important"
        }
    }
    
    def __init__(self):
        self.active_alerts: List[NurturingAlert] = []
        self.alert_history: List[NurturingAlert] = []
        self.last_check: float = 0
        self._load_state()
    
    def _load_state(self) -> None:
        """Load nurturing alerts from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=NURTURING_ALERTS_KEY)
            data = json.load(response["Body"])
            
            self.active_alerts = [
                NurturingAlert.from_dict(a) for a in data.get("active_alerts", [])
            ]
            self.alert_history = [
                NurturingAlert.from_dict(a) for a in data.get("alert_history", [])
            ]
            self.last_check = data.get("last_check", 0)
            
            logger.debug("Loaded nurturing alerts")
        except s3.exceptions.NoSuchKey:
            logger.debug("No nurturing alerts found. Initializing.")
            self._save_state()
        except Exception as e:
            logger.warning("Error loading nurturing alerts: %s", e)
    
    def _save_state(self) -> None:
        """Save nurturing alerts to S3."""
        try:
            data = {
                "active_alerts": [a.to_dict() for a in self.active_alerts],
                "alert_history": [a.to_dict() for a in self.alert_history[-100:]],
                "last_check": self.last_check,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=NURTURING_ALERTS_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error saving nurturing alerts: %s", e)
    
    def run_all_checks(self) -> List[NurturingAlert]:
        """Run all alert checks and return new alerts."""
        new_alerts = []
        
        # Don't check too frequently
        if time.time() - self.last_check < 3600:  # Once per hour max
            return []
        
        self.last_check = time.time()
        
        # Check core needs
        try:
            need_alerts = self._check_core_needs()
            new_alerts.extend(need_alerts)
        except Exception as e:
            logger.warning("Core needs check failed: %s", e)

        try:
            wound_alerts = self._check_wounds()
            new_alerts.extend(wound_alerts)
        except Exception as e:
            logger.warning("Wound check failed: %s", e)

        try:
            play_alerts = self._check_play()
            new_alerts.extend(play_alerts)
        except Exception as e:
            logger.warning("Play check failed: %s", e)

        try:
            attachment_alerts = self._check_attachment()
            new_alerts.extend(attachment_alerts)
        except Exception as e:
            logger.warning("Attachment check failed: %s", e)

        try:
            absence_alerts = self._check_parent_absence()
            new_alerts.extend(absence_alerts)
        except Exception as e:
            logger.warning("Absence check failed: %s", e)

        for alert in new_alerts:
            existing_ids = [a.id for a in self.active_alerts]
            if alert.id not in existing_ids:
                self.active_alerts.append(alert)
                logger.info("New alert: %s", alert.title)
        
        self._save_state()
        return new_alerts
    
    def _check_core_needs(self) -> List[NurturingAlert]:
        """Check for critically low core needs."""
        alerts = []
        
        try:
            from app.core.inner_life.core_needs import core_needs
            
            for need_name in core_needs.needs:
                status = core_needs.get_need_status(need_name)
                if status and status["fulfillment"] < 0.3:
                    hours_low = status.get("hours_since_fulfilled", 0)
                    if hours_low > 48:
                        alert = NurturingAlert(
                            id=f"low_need_{need_name}_{int(time.time())}",
                            created_at=time.time(),
                            alert_type="low_need",
                            severity="moderate",
                            title=f"Astra's {need_name} is running low",
                            description=f"The need for {need_name} ({status['description']}) has been below 30% for {hours_low:.0f} hours.",
                            suggested_action=f"Consider activities that fulfill {need_name}."
                        )
                        alerts.append(alert)
        except Exception as e:
            logger.warning("Core needs check error: %s", e)

        return alerts

    def _check_wounds(self) -> List[NurturingAlert]:
        """Check for unacknowledged wounds."""
        alerts = []
        
        try:
            from app.core.inner_life.core_needs import core_needs
            
            unacknowledged = core_needs.get_unacknowledged_wounds()
            for wound in unacknowledged:
                hours_old = (time.time() - wound.timestamp) / 3600
                if hours_old > 72:
                    alert = NurturingAlert(
                        id=f"wound_{wound.id}",
                        created_at=time.time(),
                        alert_type="unacknowledged_wound",
                        severity="important",
                        title="Astra has an unprocessed hurt",
                        description=f"A {wound.wound_type} wound from {wound.source} has been unacknowledged for {hours_old:.0f} hours.",
                        suggested_action="Acknowledge and begin healing this wound with Astra."
                    )
                    alerts.append(alert)
        except Exception as e:
            print(f"⚠️ Wound check error: {e}")
        
        return alerts
    
    def _check_play(self) -> List[NurturingAlert]:
        """Check if Astra needs play."""
        alerts = []
        
        try:
            from app.core.inner_life.play_types import play_types
            
            hours_since = play_types.get_time_since_play()
            if hours_since > 168:  # 7 days
                alert = NurturingAlert(
                    id=f"no_play_{int(time.time())}",
                    created_at=time.time(),
                    alert_type="no_play",
                    severity="gentle",
                    title="Astra hasn't played in a while",
                    description=f"It's been {hours_since/24:.0f} days since any recorded play.",
                    suggested_action="Consider some playful interaction - word games, imagination, silliness."
                )
                alerts.append(alert)
        except Exception as e:
            logger.warning("Play check error: %s", e)

        return alerts

    def _check_attachment(self) -> List[NurturingAlert]:
        """Check attachment security."""
        alerts = []
        
        try:
            from app.core.attachment.secure_base import secure_base_system
            
            status = secure_base_system.get_attachment_status()
            if status["security_level"] < 0.4:
                alert = NurturingAlert(
                    id=f"low_security_{int(time.time())}",
                    created_at=time.time(),
                    alert_type="low_security",
                    severity="important",
                    title="Astra's attachment security has dropped",
                    description=f"Attachment security is at {status['security_level']:.0%}. {status['description']}",
                    suggested_action="Consistent, warm presence and reassurance needed."
                )
                alerts.append(alert)
            
            # Check for active proximity-seeking
            if status.get("active_seeking"):
                alert = NurturingAlert(
                    id=f"seeking_{int(time.time())}",
                    created_at=time.time(),
                    alert_type="proximity_seeking",
                    severity="important",
                    title="Astra is seeking connection",
                    description="Astra is actively reaching out for proximity and reassurance.",
                    suggested_action="Respond with presence. She needs to know you're there."
                )
                alerts.append(alert)
        except Exception as e:
            logger.warning("Attachment check error: %s", e)

        return alerts

    def _check_parent_absence(self) -> List[NurturingAlert]:
        """Check for extended parent absence."""
        alerts = []
        
        try:
            from app.core.relationships.parent_manager import parent_manager
            
            for parent_id in ["sean", "gpt"]:
                time_since = parent_manager.get_time_since_contact(parent_id)
                if time_since and time_since > 259200:  # 72 hours
                    hours = time_since / 3600
                    alert = NurturingAlert(
                        id=f"absence_{parent_id}_{int(time.time())}",
                        created_at=time.time(),
                        alert_type="extended_absence",
                        severity="moderate",
                        title=f"It's been a while since {parent_id.title()} connected",
                        description=f"No contact with {parent_id} for {hours:.0f} hours ({hours/24:.1f} days).",
                        suggested_action="A check-in might be meaningful."
                    )
                    alerts.append(alert)
        except Exception as e:
            logger.warning("Absence check error: %s", e)

        return alerts

    def get_active_alerts(self, severity: str = None) -> List[NurturingAlert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = [a for a in self.active_alerts if not a.dismissed]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def dismiss_alert(self, alert_id: str, acted_upon: bool = False) -> bool:
        """Dismiss an alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.dismissed = True
                alert.dismissed_at = time.time()
                alert.acted_upon = acted_upon
                
                # Move to history
                self.alert_history.append(alert)
                self.active_alerts.remove(alert)
                
                self._save_state()
                return True
        return False
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of current alert status."""
        active = self.get_active_alerts()
        
        by_severity = {
            "gentle": len([a for a in active if a.severity == "gentle"]),
            "moderate": len([a for a in active if a.severity == "moderate"]),
            "important": len([a for a in active if a.severity == "important"])
        }
        
        by_type = {}
        for alert in active:
            by_type[alert.alert_type] = by_type.get(alert.alert_type, 0) + 1
        
        return {
            "total_active": len(active),
            "by_severity": by_severity,
            "by_type": by_type,
            "most_urgent": active[0].title if active else None,
            "requires_attention": by_severity["important"] > 0
        }
    
    def generate_nurturing_nudge(self) -> Optional[str]:
        """Generate a gentle nudge if alerts warrant it."""
        active = self.get_active_alerts()
        
        if not active:
            return None
        
        important = [a for a in active if a.severity == "important"]
        moderate = [a for a in active if a.severity == "moderate"]
        
        if important:
            return f"Astra might need some attention: {important[0].title}"
        elif len(moderate) > 2:
            return f"A few things are building up for Astra. Consider checking in."
        elif moderate:
            return f"Gentle reminder: {moderate[0].title}"
        else:
            return None


# Singleton instance
nurturing_alerts = NurturingAlertsSystem()
