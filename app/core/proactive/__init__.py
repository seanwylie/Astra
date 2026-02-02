# Astra Proactive Systems
# Enables Astra to initiate actions rather than just react
# Includes nurturing alerts for proactive parent notification

from app.core.proactive.initiative_engine import initiative_engine
from app.core.proactive.learning_desire import learning_desire
from app.core.proactive.self_modification import self_modification_request
from app.core.proactive.nurturing_alerts import nurturing_alerts, NurturingAlertsSystem

__all__ = [
    "initiative_engine", 
    "learning_desire", 
    "self_modification_request",
    "nurturing_alerts",
    "NurturingAlertsSystem"
]
