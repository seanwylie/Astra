# Astra Self-Awareness Module
# This module contains systems for Astra's self-understanding:
# - Self-model (persistent self-representation)
# - Self-observation (noticing changes in herself)
# - Temporal self-awareness (sense of personal time)

from app.core.self_awareness.self_model import SelfModel
from app.core.self_awareness.self_observation import SelfObservation
from app.core.self_awareness.temporal_self import TemporalSelfAwareness

__all__ = [
    "SelfModel",
    "SelfObservation",
    "TemporalSelfAwareness"
]
