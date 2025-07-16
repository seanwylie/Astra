# beta/services/__init__.py

"""
🔧 Beta Services Module
-----------------------
Centralized exports for all Astra beta services.

This module provides clean imports for all service functionality,
making it easy to use services throughout the application.

Author: Sean Wylie
Created: 2025-01-16
"""

# Core services
from .emotion_service import test_emotion_intensity, describe_current_emotions
from .lookup_service import lookup_term
from .message_processing_service import (
    process_user_message,
    send_chunked_response,
    store_concept,
    trigger_emotions_from_message
)
from .response_service import query_openai_for_response
from .personality_service import (
    personality_service,
    get_current_personality,
    get_personality_traits,
    get_response_style,
    switch_personality
)
from .enhanced_response_service import (
    generate_personality_aware_response,
    get_personality_greeting,
    get_personality_farewell
)
from .schedule_service import (
    schedule_service,
    start_schedule,
    stop_schedule,
    manual_dinner,
    manual_playtime,
    manual_dreamtime,
    get_status
)
from .spark_service import (
    begin_spark_interview,
    show_current_question,
    show_last_question,
    submit_answer,
    reflect_on_question,
    finalize_spark,
    summarize_spark,
    generate_graduation_speech
)
from .state_service import (
    get_dinner_summary,
    submit_dinner_answer,
    resolve_all_dinner_topics,
    start_dinner,
    run_playtime,
    run_dreamtime
)
from .memory_service import memory_service
from .creative_service import creative_service
from .learning_service import learning_service
from .analytics_service import analytics_service

# Service categories for easy reference
EMOTION_SERVICES = [
    'test_emotion_intensity',
    'describe_current_emotions'
]

KNOWLEDGE_SERVICES = [
    'lookup_term',
    'store_concept'
]

COMMUNICATION_SERVICES = [
    'process_user_message',
    'send_chunked_response',
    'query_openai_for_response',
    'generate_personality_aware_response',
    'get_personality_greeting',
    'get_personality_farewell'
]

PERSONALITY_SERVICES = [
    'personality_service',
    'get_current_personality',
    'get_personality_traits',
    'get_response_style',
    'switch_personality'
]

SCHEDULE_SERVICES = [
    'schedule_service',
    'start_schedule',
    'stop_schedule',
    'manual_dinner',
    'manual_playtime',
    'manual_dreamtime',
    'get_status'
]

SPARK_SERVICES = [
    'begin_spark_interview',
    'show_current_question',
    'show_last_question',
    'submit_answer',
    'reflect_on_question',
    'finalize_spark',
    'summarize_spark',
    'generate_graduation_speech'
]

STATE_SERVICES = [
    'get_dinner_summary',
    'submit_dinner_answer',
    'resolve_all_dinner_topics',
    'start_dinner',
    'run_playtime',
    'run_dreamtime'
]

MEMORY_SERVICES = [
    'memory_service'
]

CREATIVE_SERVICES = [
    'creative_service'
]

LEARNING_SERVICES = [
    'learning_service'
]

ANALYTICS_SERVICES = [
    'analytics_service'
]

# All available services
ALL_SERVICES = (
    EMOTION_SERVICES + 
    KNOWLEDGE_SERVICES + 
    COMMUNICATION_SERVICES + 
    PERSONALITY_SERVICES +
    SCHEDULE_SERVICES + 
    SPARK_SERVICES + 
    STATE_SERVICES +
    MEMORY_SERVICES +
    CREATIVE_SERVICES +
    LEARNING_SERVICES +
    ANALYTICS_SERVICES
)

__all__ = ALL_SERVICES