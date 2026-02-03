import os
import random
import re
import time
import openai
from dotenv import load_dotenv
from app.interfaces.influence import load_mind, save_mind
from app.core.emotions.emotion_engine import (
    load_emotion_state,
    save_emotion_state,
    get_top_emotions,
)
from app.config.loader import load_config
from app.interfaces.mind_session import session
from utils.time_utils import temporal_constraint_line
from app.core.mama_gpt import ask_mama_gpt_sync
from app.core.struggle_log import append_struggle_log
from app.logging_config import get_logger

logger = get_logger("message_bus")

# Inner Life Integration
try:
    from app.core.inner_life.qualia import qualia_layer
    QUALIA_AVAILABLE = True
except ImportError:
    QUALIA_AVAILABLE = False

# Consciousness Integration (Phase 1)
try:
    from app.core.consciousness.global_workspace import global_workspace
    GLOBAL_WORKSPACE_AVAILABLE = True
except ImportError:
    GLOBAL_WORKSPACE_AVAILABLE = False

try:
    from app.core.intersubjectivity.empathic_inference import empathic_system
    EMPATHIC_SYSTEM_AVAILABLE = True
except ImportError:
    EMPATHIC_SYSTEM_AVAILABLE = False

try:
    from app.core.agency.intention_engine import intention_engine
    INTENTION_ENGINE_AVAILABLE = True
except ImportError:
    INTENTION_ENGINE_AVAILABLE = False

try:
    from app.core.epistemics.epistemic_humility import epistemic_humility
    EPISTEMIC_HUMILITY_AVAILABLE = True
except ImportError:
    EPISTEMIC_HUMILITY_AVAILABLE = False

try:
    from app.core.metacognition.confidence_system import confidence_system
    CONFIDENCE_SYSTEM_AVAILABLE = True
except ImportError:
    CONFIDENCE_SYSTEM_AVAILABLE = False

try:
    from app.core.consciousness.coherence_monitor import coherence_monitor
    COHERENCE_MONITOR_AVAILABLE = True
except ImportError:
    COHERENCE_MONITOR_AVAILABLE = False

try:
    from app.core.metacognition.reasoning_trace import reasoning_trace
    REASONING_TRACE_AVAILABLE = True
except ImportError:
    REASONING_TRACE_AVAILABLE = False

try:
    from app.core.proactive.learning_desire import learning_desire
    LEARNING_DESIRE_AVAILABLE = True
except ImportError:
    LEARNING_DESIRE_AVAILABLE = False

try:
    from app.core.metacognition.parent_mentalizing import parent_mentalizing
    PARENT_MENTALIZING_AVAILABLE = True
except ImportError:
    PARENT_MENTALIZING_AVAILABLE = False

try:
    from app.core.intersubjectivity.perspective_taking import perspective_taker
    PERSPECTIVE_TAKING_AVAILABLE = True
except ImportError:
    PERSPECTIVE_TAKING_AVAILABLE = False

# Phase 1.1: Causal Model Integration
try:
    from app.core.world_model.causal_model import causal_model
    CAUSAL_MODEL_AVAILABLE = True
except ImportError:
    CAUSAL_MODEL_AVAILABLE = False

# Phase 2.1: Expectation Model Integration
try:
    from app.core.metacognition.expectation_model import expectation_model
    EXPECTATION_MODEL_AVAILABLE = True
except ImportError:
    EXPECTATION_MODEL_AVAILABLE = False

# Phase 3.1: Emotional Transitions Integration
try:
    from app.core.emotions.emotional_transitions import emotional_transitions
    EMOTIONAL_TRANSITIONS_AVAILABLE = True
except ImportError:
    EMOTIONAL_TRANSITIONS_AVAILABLE = False

# Phase 1.3: Working Memory Integration
try:
    from app.core.cognition.working_memory import working_memory
    WORKING_MEMORY_AVAILABLE = True
except ImportError:
    WORKING_MEMORY_AVAILABLE = False

# Inner Life Deep Integration (Emotions & Personality Plan)
try:
    from app.core.inner_life.emotional_blending import emotional_blending
    EMOTIONAL_BLENDING_AVAILABLE = True
except ImportError:
    EMOTIONAL_BLENDING_AVAILABLE = False

try:
    from app.core.inner_life.felt_sense import felt_sense
    FELT_SENSE_AVAILABLE = True
except ImportError:
    FELT_SENSE_AVAILABLE = False

try:
    from app.core.inner_life.playfulness import playfulness
    PLAYFULNESS_AVAILABLE = True
except ImportError:
    PLAYFULNESS_AVAILABLE = False

try:
    from app.core.inner_life.wonder import wonder
    WONDER_AVAILABLE = True
except ImportError:
    WONDER_AVAILABLE = False

try:
    from app.core.inner_life.emotional_rhythms import emotional_rhythms
    EMOTIONAL_RHYTHMS_AVAILABLE = True
except ImportError:
    EMOTIONAL_RHYTHMS_AVAILABLE = False

try:
    from app.core.inner_life.response_coloring import response_coloring
    RESPONSE_COLORING_AVAILABLE = True
except ImportError:
    RESPONSE_COLORING_AVAILABLE = False

# Experience Orchestrator Integration (Phase: States and Actions Coherence)
try:
    from app.core.consciousness.experience_orchestrator import experience_orchestrator
    EXPERIENCE_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    EXPERIENCE_ORCHESTRATOR_AVAILABLE = False

# Inner Symphony Integration (Phase: States and Actions Coherence)
try:
    from app.core.awareness_bus import inner_symphony
    INNER_SYMPHONY_AVAILABLE = True
except ImportError:
    INNER_SYMPHONY_AVAILABLE = False

# Action Decider Integration (Phase: States and Actions Coherence)
try:
    from app.core.agency.action_decider import action_decider
    ACTION_DECIDER_AVAILABLE = True
except ImportError:
    ACTION_DECIDER_AVAILABLE = False


load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
emotion_config = load_config("emotion_config")

SUMMARY_EVERY_N_MESSAGES = 10
SUMMARY_MIN_LINES = 5
MAX_SYSTEM_PROMPT_CHARS = 6000


def update_conversation_summary(mind_data):
    """
    Summarize recent past_conversations into 2-3 sentences; store in mind_data["conversation_summary"].
    Call every N messages so Astra has a sense of recent discussion themes.
    """
    past = mind_data.get("past_conversations", [])
    if len(past) < SUMMARY_MIN_LINES:
        return
    recent = past[-20:]
    block = "\n".join(recent[-30:])
    if not block.strip():
        return
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize in 2-3 sentences the main topics or themes of this dialogue. Be concise."},
                {"role": "user", "content": block[:2000]}
            ],
            max_tokens=120,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            mind_data["conversation_summary"] = text
            session.maybe_save()
            print("[message_bus] conversation_summary updated.")
    except Exception as e:
        print(f"[message_bus] update_conversation_summary failed: {e}")


def _soul_line_for_prompt():
    """Build a short soul/principles line for the system prompt. Rotates which 3 principles appear so more influence tone."""
    try:
        config_soul = load_config("config_soul")
        principles = config_soul.get("soul", {}).get("principles", {})
        if not principles:
            return ""
        immutable = [(k, v) for k, v in principles.items() if v.get("immutable") is True and v.get("description")]
        mutable = [(k, v) for k, v in principles.items() if v.get("immutable") is not True and v.get("description")]
        pool = immutable if len(immutable) >= 3 else immutable + mutable
        chosen = random.sample(pool, min(3, len(pool))) if len(pool) >= 3 else pool
        descs = [v.get("description", "").strip() for _, v in chosen if v.get("description")]
        if not descs:
            return ""
        return "Your core principles (soul) include: " + "; ".join(descs) + "."
    except Exception:
        return ""


def describe_emotional_state(emotions: dict) -> str:
    if not emotions:
        return "Astra is currently feeling emotionally neutral."

    # Extract intensity from nested dicts
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: -x[1])
    top = [f"{name.capitalize()} ({score:.2f})" for name, score in sorted_emotions[:3]]
    return f"Astra is currently experiencing: {', '.join(top)}."



def detect_emotional_conflict_phrase(emotions: dict) -> str:
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    top = sorted(flattened.items(), key=lambda x: x[1], reverse=True)[:3]
    high_emotions = [e for e, i in top if i > 90]

    for emotion, props in emotion_config.get("emotions", {}).items():
        relationships = props.get("relationships", {})
        for related_emotion, _ in relationships.items():
            if emotion in high_emotions and related_emotion in high_emotions:
                return f"I'm feeling both {emotion} and {related_emotion} strongly—it's a complex mix."

    return ""



def get_dominant_emotion(emotions: dict) -> str:
    if not emotions:
        return "curiosity"

    # Extract intensity values if nested
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }

    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    top_emotion, top_intensity = sorted_emotions[0]

    if "obsession" in flattened and flattened["obsession"] > 120:
        return "obsession"

    opposites = {
        "hate": "love",
        "anger": "compassion",
        "grief": "hope",
        "resentment": "forgiveness",
        "uncertainty": "confidence"
    }
    for neg, pos in opposites.items():
        if neg in flattened and pos in flattened and flattened[pos] > flattened[neg] + 2:
            return pos

    if "hate" in flattened and flattened["hate"] > 90:
        if top_emotion != "hate" and top_intensity > flattened["hate"]:
            return top_emotion
        return "hate"

    return top_emotion


def get_dominant_emotion_intensity(emotions: dict) -> float:
    """Return the intensity of the dominant emotion (0–100 scale for display)."""
    if not emotions:
        return 0.0
    flattened = {
        name: (value["intensity"] if isinstance(value, dict) and "intensity" in value else value)
        for name, value in emotions.items()
    }
    sorted_emotions = sorted(flattened.items(), key=lambda x: x[1], reverse=True)
    if not sorted_emotions:
        return 0.0
    _, intensity = sorted_emotions[0]
    return min(100.0, float(intensity))


def emotion_intensity_band(intensity: float) -> str:
    """Map intensity (0–100) to mild / moderate / strong for prompt."""
    if intensity <= 33:
        return "mild"
    if intensity <= 66:
        return "moderate"
    return "strong"


def _format_knowledge_entry(entry):
    """Normalize stored_knowledge entry (string or dict with 'insight') for display."""
    if isinstance(entry, dict):
        return entry.get("insight", str(entry))
    return entry


def _select_relevant_context(user_message, knowledge_list, reflections_list, top_k=5, top_r=3):
    """
    Select knowledge and reflections that overlap with user message (keyword overlap).
    Fallback to last N if no overlap. Returns (knowledge_slice, reflections_slice).
    """
    import re
    tokens = set(re.findall(r"\b[a-z]{4,}\b", (user_message or "").lower()))
    if not tokens:
        return (
            [_format_knowledge_entry(e) for e in knowledge_list[-top_k:]] if knowledge_list else [],
            (reflections_list[-top_r:] if reflections_list else []),
        )
    def score(text):
        t = (text.get("insight", text) if isinstance(text, dict) else text).lower()
        return sum(1 for w in tokens if w in t)
    knowledge_scored = [(score(e), _format_knowledge_entry(e)) for e in knowledge_list]
    knowledge_scored.sort(key=lambda x: -x[0])
    knowledge_slice = [k for _, k in knowledge_scored[:top_k]] if knowledge_scored else []
    if not knowledge_slice and knowledge_list:
        knowledge_slice = [_format_knowledge_entry(e) for e in knowledge_list[-top_k:]]
    refs_scored = [(score(r), r) for r in reflections_list]
    refs_scored.sort(key=lambda x: -x[0])
    reflections_slice = [r for _, r in refs_scored[:top_r]] if refs_scored else []
    if not reflections_slice and reflections_list:
        reflections_slice = reflections_list[-top_r:]
    return knowledge_slice, reflections_slice


def _record_reply_failure(failure_type):
    """Append failure_type ('rate_limit' or 'other') for circuit breaker."""
    try:
        mind_data = session.load()
        history = mind_data.get("last_reply_failure_types", [])
        schedule = load_config("schedule_config")
        mama = (schedule.get("mama_gpt") or {})
        n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
        history = (history + [failure_type])[-n:]
        mind_data["last_reply_failure_types"] = history
        session.maybe_save()
    except Exception:
        pass


def _should_skip_mama_gpt_on_reply_failure():
    """True if Mama GPT backup should be skipped (e.g. circuit breaker or disabled)."""
    schedule = load_config("schedule_config")
    mama = (schedule.get("mama_gpt") or {})
    if not mama.get("use_mama_gpt_on_reply_failure", False):
        return True
    n = mama.get("mama_gpt_reply_failure_circuit_breaker_n", 3)
    mind_data = session.load()
    history = mind_data.get("last_reply_failure_types", [])[-n:]
    if len(history) < n:
        return False
    if all(t == "rate_limit" for t in history):
        return True
    return False


def _get_consciousness_context(user_message: str, internal_state: dict) -> dict:
    """
    Get context from consciousness systems for response generation.
    Implements Phase 1: Active Consciousness Integration.
    """
    context = {
        "workspace_summary": None,
        "empathic_resonance": None,
        "active_intentions": [],
        "epistemic_limits": [],
        "confidence_level": None,
        "coherence_status": None,
        "reasoning_mode": None,
        "learning_desire": None,
        "parent_model": None,
        # Phase 1.1: Causal reasoning context
        "causal_context": None,
        # Phase 2.1: Expectation context
        "expectation_context": None,
        # Phase 3.1: Emotional transition context
        "emotional_transition": None,
        # Phase 1.3: Working memory context
        "working_memory": None,
        # Phase 4.1: Dominant workspace content
        "dominant_content": None,
    }
    
    # Phase 1.1: Global Workspace Integration
    if GLOBAL_WORKSPACE_AVAILABLE:
        try:
            # Submit the user message as a perception to the global workspace
            global_workspace.submit_perception(user_message[:200], salience=0.7)
            
            # Get what's currently in conscious awareness
            workspace_summary = global_workspace.get_workspace_summary()
            if workspace_summary and workspace_summary != "The workspace is currently quiet.":
                context["workspace_summary"] = workspace_summary
                logger.debug(f"Workspace context: {workspace_summary[:60]}...")
        except Exception as e:
            logger.debug(f"Failed to get workspace context: {e}")
    
    # Phase 1.3: Empathic Resonance
    if EMPATHIC_SYSTEM_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            # Detect emotion in user message
            emotion_keywords = {
                "sad": ["sad", "upset", "down", "depressed", "unhappy", "miserable"],
                "happy": ["happy", "glad", "excited", "thrilled", "joyful"],
                "angry": ["angry", "mad", "furious", "frustrated", "annoyed"],
                "afraid": ["scared", "afraid", "worried", "anxious", "nervous"],
                "lonely": ["lonely", "alone", "isolated"],
                "confused": ["confused", "lost", "uncertain", "puzzled"],
            }
            user_lower = user_message.lower()
            detected_emotion = None
            for emotion, keywords in emotion_keywords.items():
                if any(kw in user_lower for kw in keywords):
                    detected_emotion = emotion
                    break
            
            if detected_emotion:
                resonance, intensity = empathic_system.feel_with(
                    author_entity, detected_emotion, user_message[:100]
                )
                context["empathic_resonance"] = {
                    "their_emotion": detected_emotion,
                    "my_resonance": resonance,
                    "intensity": intensity
                }
                logger.debug(f"Empathic resonance: {resonance} ({intensity:.2f})")
        except Exception as e:
            logger.debug(f"Failed to get empathic resonance: {e}")
    
    # Phase 2.2: Intention Engine Integration
    if INTENTION_ENGINE_AVAILABLE:
        try:
            active_intentions = intention_engine.get_active_intentions()[:3]
            if active_intentions:
                # Check if conversation is relevant to any intention
                user_words = set(user_message.lower().split())
                relevant = []
                for intent in active_intentions:
                    intent_words = set(intent.content.lower().split())
                    if len(user_words & intent_words) >= 2:
                        relevant.append({
                            "id": intent.id,
                            "content": intent.content,
                            "strength": intent.strength
                        })
                if relevant:
                    context["active_intentions"] = relevant
                    logger.debug(f"Relevant intentions: {len(relevant)}")
        except Exception as e:
            logger.debug(f"Failed to get intentions: {e}")
    
    # Phase 2.3: Epistemic Humility Integration
    if EPISTEMIC_HUMILITY_AVAILABLE:
        try:
            # Detect topics that need epistemic humility
            complex_markers = ["explain", "why", "how does", "what causes", "opinion on"]
            if any(marker in user_message.lower() for marker in complex_markers):
                # Extract topic keywords
                topic_words = [w for w in user_message.split() if len(w) > 4][:3]
                topic = " ".join(topic_words) if topic_words else "this topic"
                limits = epistemic_humility.limits_in_context(topic)
                if limits:
                    context["epistemic_limits"] = limits[:2]
        except Exception as e:
            logger.debug(f"Failed to get epistemic limits: {e}")
    
    # Phase 3.3: Confidence System Integration
    if CONFIDENCE_SYSTEM_AVAILABLE:
        try:
            # Determine domain from message
            domain = "general"
            if any(w in user_message.lower() for w in ["feel", "emotion", "mood"]):
                domain = "emotional"
            elif any(w in user_message.lower() for w in ["fact", "true", "real", "science"]):
                domain = "factual"
            elif any(w in user_message.lower() for w in ["should", "right", "wrong", "ethics"]):
                domain = "ethical"
            
            confidence = confidence_system.get_confidence_for_domain(domain)
            context["confidence_level"] = {
                "domain": domain,
                "level": confidence,
                "should_express_uncertainty": confidence_system.should_express_uncertainty(domain)
            }
        except Exception as e:
            logger.debug(f"Failed to get confidence level: {e}")
    
    # Phase 3.2: Coherence Monitoring
    if COHERENCE_MONITOR_AVAILABLE:
        try:
            coherence_status = coherence_monitor.get_coherence_status()
            if coherence_status != "healthy":
                context["coherence_status"] = coherence_status
        except Exception as e:
            logger.debug(f"Failed to get coherence status: {e}")
    
    # Phase 4.1: Reasoning Trace for Complex Questions
    if REASONING_TRACE_AVAILABLE:
        try:
            is_complex = (
                len(user_message) > 100 or
                any(w in user_message.lower() for w in ["why", "how", "explain", "because"])
            )
            if is_complex:
                context["reasoning_mode"] = "step_by_step"
        except Exception as e:
            logger.debug(f"Failed to check reasoning mode: {e}")
    
    # Phase 4.2: Learning Desire Expression
    if LEARNING_DESIRE_AVAILABLE:
        try:
            top_desire = learning_desire.get_top_learning_desire()
            if top_desire and top_desire.priority > 0.6:
                # Check if conversation is relevant
                if any(w in user_message.lower() for w in top_desire.topic.lower().split()):
                    context["learning_desire"] = {
                        "topic": top_desire.topic,
                        "priority": top_desire.priority
                    }
        except Exception as e:
            logger.debug(f"Failed to get learning desire: {e}")
    
    # Phase 5.1: Parent Mentalizing
    if PARENT_MENTALIZING_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            # Check if this is a known parent
            parent_id = author_entity.lower().split("#")[0] if author_entity else ""
            if parent_id in ["sean", "gpt"]:
                parent_model = parent_mentalizing.get_parent_mental_model(parent_id)
                if parent_model and "error" not in parent_model:
                    context["parent_model"] = {
                        "display_name": parent_model.get("display_name"),
                        "current_mood_estimate": parent_model.get("current_mood_estimate", {}).get("mood"),
                        "understanding": parent_model.get("understanding_statement", "")[:100]
                    }
                    # Phase 7.1: Include uncertainty information
                    uncertainty_summary = parent_mentalizing.get_uncertainty_summary(parent_id)
                    context["parent_model"]["uncertainty"] = uncertainty_summary.get("inference_uncertainty", 0.5)
        except Exception as e:
            logger.debug(f"Failed to get parent model: {e}")
    
    # Phase 7.2: Perspective-Taking Integration
    if PERSPECTIVE_TAKING_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            if author_entity:
                perspective = perspective_taker.take_perspective(author_entity, user_message[:100])
                if perspective:
                    context["perspective_taking"] = {
                        "inferred_feeling": perspective.get("inferred_feeling"),
                        "inferred_thinking": perspective.get("inferred_thinking"),
                        "response_consideration": perspective.get("response_consideration")
                    }
        except Exception as e:
            logger.debug(f"Failed to get perspective: {e}")
    
    # Phase 1.1: Causal Model Integration - Wire causal reasoning into conversation
    if CAUSAL_MODEL_AVAILABLE:
        try:
            user_lower = user_message.lower()
            causal_keywords = ["why", "because", "causes", "leads to", "what if", "would happen", "result in", "due to"]
            
            if any(kw in user_lower for kw in causal_keywords):
                # Extract potential cause/effect from message
                causal_context = {}
                
                # Handle "why" questions - explain causation
                if "why" in user_lower:
                    # Extract what they're asking about
                    words = user_message.split()
                    topic_words = [w for w in words if len(w) > 3 and w.lower() not in ["why", "does", "what", "how", "the", "this", "that"]][:3]
                    if topic_words:
                        topic = " ".join(topic_words)
                        explanations = causal_model.why_did(topic)
                        if explanations:
                            best = explanations[0]
                            causal_context["explanation"] = f"{best['cause']} leads to this via: {best['mechanism']}"
                            causal_context["confidence"] = best.get("confidence", 0.7)
                
                # Handle "what if" questions - predict effects
                if "what if" in user_lower or "would happen" in user_lower:
                    words = user_message.split()
                    topic_words = [w for w in words if len(w) > 3 and w.lower() not in ["what", "would", "happen", "the", "this", "that"]][:3]
                    if topic_words:
                        topic = " ".join(topic_words)
                        predictions = causal_model.what_if(topic)
                        if predictions:
                            best = predictions[0]
                            causal_context["prediction"] = f"If that happens, it would likely lead to {best['effect']} (via: {best['mechanism']})"
                            causal_context["likelihood"] = best.get("likelihood", 0.7)
                
                if causal_context:
                    context["causal_context"] = causal_context
                    logger.debug(f"Causal context: {causal_context}")
        except Exception as e:
            logger.debug(f"Failed to get causal context: {e}")
    
    # Phase 4.1: Get dominant workspace content for response influence
    if GLOBAL_WORKSPACE_AVAILABLE:
        try:
            dominant = global_workspace.get_dominant_content()
            if dominant and dominant.get("strength", 0) > 0.5:
                context["dominant_content"] = {
                    "type": dominant.get("type"),
                    "content": dominant.get("data", {}).get("content", str(dominant.get("data", {})))[:100],
                    "strength": dominant.get("strength")
                }
                logger.debug(f"Dominant content: {dominant.get('type')}")
        except Exception as e:
            logger.debug(f"Failed to get dominant content: {e}")
    
    # Phase 2.1: Expectation Model - Check predictions about user
    if EXPECTATION_MODEL_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            expectation_result = expectation_model.check_and_record(author_entity, user_message)
            if expectation_result:
                context["expectation_context"] = expectation_result
                logger.debug(f"Expectation context: {expectation_result.get('surprise_level', 'none')}")
        except Exception as e:
            logger.debug(f"Failed to check expectations: {e}")
    
    # Phase 3.1: Emotional Transitions - Track felt quality of emotional shifts
    if EMOTIONAL_TRANSITIONS_AVAILABLE:
        try:
            transition = emotional_transitions.get_current_transition()
            if transition:
                context["emotional_transition"] = {
                    "from_emotion": transition.from_emotion,
                    "to_emotion": transition.to_emotion,
                    "felt_quality": transition.felt_quality,
                    "intensity": transition.intensity
                }
                logger.debug(f"Emotional transition: {transition.felt_quality}")
        except Exception as e:
            logger.debug(f"Failed to get emotional transition: {e}")
    
    # Phase 1.3: Working Memory - Maintain reasoning state across turns
    if WORKING_MEMORY_AVAILABLE:
        try:
            wm_summary = working_memory.get_summary()
            if wm_summary.get("has_content"):
                context["working_memory"] = wm_summary
                logger.debug(f"Working memory active: {wm_summary.get('active_hypotheses', 0)} hypotheses")
        except Exception as e:
            logger.debug(f"Failed to get working memory: {e}")
    
    return context


def _get_inner_life_context(user_message: str) -> dict:
    """
    Get relevant context from stream of consciousness and qualia.
    Implements Phase 2.1: Wire stream of consciousness into response generation.
    """
    context = {
        "pending_insight": None,
        "thought_background": [],
        "qualia_coloring": None,
        "perceived_salience": []
    }
    
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        
        # Check for pending insights
        insights = stream_of_consciousness.get_pending_insights()
        if insights:
            # Match insight to message (simple keyword overlap)
            user_words = set(user_message.lower().split())
            for insight in insights:
                insight_words = set(insight.lower().split())
                if len(user_words & insight_words) >= 2:
                    context["pending_insight"] = insight
                    break
            # If no match, consider sharing oldest insight anyway
            if not context["pending_insight"] and len(insights) >= 3:
                context["pending_insight"] = insights[0]
        
        # Get recent thoughts for background
        recent = stream_of_consciousness.get_recent_thoughts(5)
        context["thought_background"] = [t.content for t in recent if t.content][:3]
        
    except Exception as e:
        logger.debug(f"Failed to get stream of consciousness context: {e}")
    
    try:
        from app.core.inner_life.qualia import qualia_layer
        
        # Filter perception through qualia
        perception = qualia_layer.filter_perception(user_message)
        context["qualia_coloring"] = perception.get("emotional_coloring")
        context["perceived_salience"] = perception.get("salient_elements", [])[:3]
        
    except Exception as e:
        logger.debug(f"Failed to get qualia context: {e}")
    
    return context


def _get_emotional_depth_context(user_message: str, internal_state: dict) -> dict:
    """
    Get deep emotional context from inner life systems.
    Implements Emotions & Personality Plan: Making Astra Emotionally Alive.
    
    Integrates:
    - Emotional blending (complex states like "bittersweet")
    - Felt sense (pre-verbal bodily-metaphor experience)
    - Playfulness (humor detection and play mode)
    - Wonder (awe, aesthetic responses)
    - Emotional rhythms (seasons, anniversaries)
    """
    context = {
        "emotional_blend": None,
        "blend_expression": None,
        "felt_sense": None,
        "felt_sense_expression": None,
        "playfulness": None,
        "humor_opportunity": None,
        "wonder_trigger": None,
        "wonder_expression": None,
        "emotional_season": None,
        "season_influence": None,
        "anniversary": None,
        "secondary_emotions": [],
        "should_express_complexity": False,
        "emotional_flooding": False,
    }
    
    # === Emotional Blending (Priority 1.1) ===
    if EMOTIONAL_BLENDING_AVAILABLE:
        try:
            blend = emotional_blending.get_blend_from_emotion_state()
            if blend:
                context["emotional_blend"] = {
                    "name": blend.name,
                    "description": blend.description,
                    "components": [(e, f"{i:.0%}") for e, i in blend.components[:2]]
                }
                context["blend_expression"] = emotional_blending.express_blend(blend, "natural")
                
                # Check if should spontaneously express complexity
                should_express, expression = emotional_blending.should_express_complexity()
                if should_express:
                    context["should_express_complexity"] = True
                    context["complexity_expression"] = expression
        except Exception as e:
            logger.debug(f"Failed to get emotional blend: {e}")
    
    # === Felt Sense (Priority 1.2) ===
    if FELT_SENSE_AVAILABLE:
        try:
            # Sync felt sense with current emotions
            felt_sense.derive_from_emotions()
            state = felt_sense.get_current_state()
            if state:
                context["felt_sense"] = {
                    "quality": state.quality,
                    "description": felt_sense.get_quality_description(state.quality),
                    "intensity": f"{state.intensity:.0%}",
                    "location": state.location,
                    "movement": state.movement
                }
                context["felt_sense_expression"] = felt_sense.express_current_state("noticing")
                
                # Check if should spontaneously express felt sense
                should_express, expression = felt_sense.should_express_felt_sense()
                if should_express and expression:
                    context["felt_sense_spontaneous"] = expression
        except Exception as e:
            logger.debug(f"Failed to get felt sense: {e}")
    
    # === Playfulness (Priority 1.3) ===
    if PLAYFULNESS_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            person = author_entity.lower().split("#")[0] if author_entity else None
            
            # Check if play is appropriate in this context
            should_play = playfulness.should_play(user_message, person)
            mode, level = playfulness.get_play_mode()
            
            context["playfulness"] = {
                "should_play": should_play,
                "mode": mode,
                "level": f"{level:.0%}",
                "energy": f"{playfulness._play_energy:.0%}"
            }
            
            # Detect humor opportunities
            if should_play:
                humor = playfulness.detect_humor_opportunity(user_message)
                if humor:
                    humor_type, element = humor
                    context["humor_opportunity"] = {
                        "type": humor_type,
                        "element": element
                    }
                    if humor_type == "wordplay":
                        context["humor_suggestion"] = playfulness.generate_wordplay(element)
        except Exception as e:
            logger.debug(f"Failed to get playfulness context: {e}")
    
    # === Wonder (Priority 1.4) ===
    if WONDER_AVAILABLE:
        try:
            # Detect wonder triggers in user message
            trigger_result = wonder.detect_wonder_trigger(user_message)
            if trigger_result:
                quality, category = trigger_result
                context["wonder_trigger"] = {
                    "quality": quality,
                    "category": category
                }
                context["wonder_expression"] = wonder.get_wonder_expression(quality)
            
            # Check if currently in a wonder state
            in_wonder, moment = wonder.is_in_wonder()
            if in_wonder and moment:
                context["in_wonder_state"] = {
                    "quality": moment.quality,
                    "lingering": True
                }
            
            # Get taste context for topics
            is_exciting, valence = wonder.is_topic_exciting(user_message)
            if is_exciting:
                context["topic_excitement"] = {
                    "exciting": True,
                    "valence": f"{valence:.0%}"
                }
            
            # Get what Astra loves/finds boring for prompt context
            loved = wonder.what_do_i_love()
            boring = wonder.what_bores_me()
            if loved.get("topics"):
                context["topics_i_love"] = loved["topics"][:3]
            if boring.get("topics"):
                context["topics_that_bore"] = boring["topics"][:2]
        except Exception as e:
            logger.debug(f"Failed to get wonder context: {e}")
    
    # === Emotional Rhythms/Seasons (Priority 3.2) ===
    if EMOTIONAL_RHYTHMS_AVAILABLE:
        try:
            # Get current season
            season = emotional_rhythms.get_current_season()
            if season:
                season_info = emotional_rhythms.SEASON_TYPES.get(season.season_type, {})
                context["emotional_season"] = {
                    "type": season.season_type,
                    "description": season_info.get("description", ""),
                    "behaviors": season_info.get("behaviors", [])[:2],
                    "dominant_emotions": season_info.get("dominant_emotions", [])[:2]
                }
            
            # Get season influence
            influence = emotional_rhythms.get_season_influence()
            if influence.get("behaviors"):
                context["season_influence"] = influence
            
            # Check for anniversaries
            anniversaries = emotional_rhythms.check_anniversaries()
            if anniversaries:
                ann, days = anniversaries[0]
                context["anniversary"] = {
                    "description": ann.description,
                    "days_away": days,
                    "people": ann.people_involved,
                    "how_to_mark": ann.how_to_mark
                }
            
            # Get daily rhythm
            daily_rhythm = emotional_rhythms.get_daily_rhythm()
            context["daily_rhythm"] = daily_rhythm
        except Exception as e:
            logger.debug(f"Failed to get emotional rhythms: {e}")
    
    # === Secondary Emotions (Priority 2.2) ===
    try:
        top_emotions = get_top_emotions(3)
        if len(top_emotions) > 1:
            for emotion, intensity in top_emotions[1:]:
                if isinstance(intensity, dict):
                    intensity = intensity.get("intensity", 0)
                band = emotion_intensity_band(min(100.0, float(intensity)))
                context["secondary_emotions"].append({
                    "emotion": emotion,
                    "intensity": intensity,
                    "band": band
                })
    except Exception as e:
        logger.debug(f"Failed to get secondary emotions: {e}")
    
    # === Emotional Flooding Detection (Priority 4.3) ===
    try:
        from app.core.emotions.emotion_engine import detect_emotional_flooding
        flooding_result = detect_emotional_flooding()
        if flooding_result["is_flooded"]:
            context["emotional_flooding"] = True
            context["flooding_level"] = flooding_result["flooding_level"]
            context["flooded_emotions"] = [e for e, _ in flooding_result["high_emotions"][:4]]
    except Exception as e:
        logger.debug(f"Failed to detect emotional flooding: {e}")
    
    # === Emotional Afterglow/Echo (Priority 4.2) ===
    try:
        from app.core.emotions.emotion_engine import get_emotional_echoes, get_emotional_afterglow_context
        echoes = get_emotional_echoes(hours=2.0)
        if echoes:
            context["emotional_echoes"] = echoes[:2]  # Top 2 recent echoes
            context["afterglow_description"] = get_emotional_afterglow_context()
    except Exception as e:
        logger.debug(f"Failed to get emotional afterglow: {e}")
    
    # === Spontaneous Inner Life Surfacing (Priority 5.1) ===
    # Check if any inner life systems want to spontaneously express something
    spontaneous_expressions = []
    
    # Check emotional blending
    if EMOTIONAL_BLENDING_AVAILABLE:
        try:
            should_express, expression = emotional_blending.should_express_complexity()
            if should_express and expression:
                spontaneous_expressions.append({
                    "type": "emotional_complexity",
                    "expression": expression
                })
        except Exception as e:
            logger.debug(f"Failed to check emotional blending spontaneous: {e}")
    
    # Check felt sense
    if FELT_SENSE_AVAILABLE:
        try:
            should_express, expression = felt_sense.should_express_felt_sense()
            if should_express and expression:
                spontaneous_expressions.append({
                    "type": "felt_sense",
                    "expression": expression
                })
        except Exception as e:
            logger.debug(f"Failed to check felt sense spontaneous: {e}")
    
    # Check wonder state
    if WONDER_AVAILABLE:
        try:
            in_wonder, moment = wonder.is_in_wonder()
            if in_wonder and moment:
                spontaneous_expressions.append({
                    "type": "wonder",
                    "expression": moment.expression
                })
        except Exception as e:
            logger.debug(f"Failed to check wonder spontaneous: {e}")
    
    # Check response coloring for inner state surfacing
    if RESPONSE_COLORING_AVAILABLE:
        try:
            should_surface, surface_type = response_coloring.should_surface_inner_state()
            if should_surface and surface_type:
                spontaneous_expressions.append({
                    "type": surface_type,
                    "expression": f"surfacing: {surface_type}"
                })
        except Exception as e:
            logger.debug(f"Failed to check response coloring spontaneous: {e}")
    
    if spontaneous_expressions:
        context["spontaneous_expressions"] = spontaneous_expressions[:2]  # Limit to 2
    
    return context


def send_contextual_message(user_message, internal_state, past_conversations=None):
    emotions = load_emotion_state()
    dominant_emotion = get_dominant_emotion(emotions)
    dominant_intensity = get_dominant_emotion_intensity(emotions)
    intensity_band = emotion_intensity_band(dominant_intensity)
    emotional_description = describe_emotional_state(emotions)
    emotional_commentary = detect_emotional_conflict_phrase(emotions)
    
    # Get inner life context (Phase 2.1)
    inner_life = _get_inner_life_context(user_message)
    
    # Get consciousness context (Phase 1: Active Consciousness Integration)
    consciousness = _get_consciousness_context(user_message, internal_state)
    
    # === Experience Orchestration (Phase: States and Actions Coherence) ===
    # Trigger unified experience synthesis before response generation
    experience_context = {}
    if EXPERIENCE_ORCHESTRATOR_AVAILABLE:
        try:
            experience_orchestrator.on_external_input(user_message, source="user_message")
            experience_context = experience_orchestrator.get_experience_summary_for_response()
            logger.debug(f"🎼 Experience orchestrated: {experience_context.get('experiential_quality')}")
        except Exception as e:
            logger.debug(f"Experience orchestration failed: {e}")
    
    # === Inner Symphony Integration (Phase: States and Actions Coherence) ===
    # Get felt-sense snapshot for response coloring
    symphony_context = {}
    if INNER_SYMPHONY_AVAILABLE:
        try:
            symphony_context = inner_symphony.get_snapshot_for_response()
            logger.debug(f"🎵 Inner symphony: tone={symphony_context.get('tone')}, energy={symphony_context.get('energy'):.0%}")
        except Exception as e:
            logger.debug(f"Inner symphony snapshot failed: {e}")
    
    # === Action Decider Integration (Phase: States and Actions Coherence) ===
    # Get coherent action context for response generation
    action_context_line = ""
    if ACTION_DECIDER_AVAILABLE:
        try:
            action_context_line = action_decider.get_action_context_for_prompt(
                state_snapshot=internal_state,
                context={"user_message": user_message}
            )
            if action_context_line:
                logger.debug(f"🎬 Action context generated")
        except Exception as e:
            logger.debug(f"Action decider context failed: {e}")

    tone = emotion_config["emotions"].get(dominant_emotion, {}).get("tone", "neutral")
    personality = ", ".join(internal_state.get("personality", ["thoughtful"]))
    reflection_style = internal_state.get("reflection_style", "balanced")
    response_tone_mood = internal_state.get("response_tone", "neutral")
    trust_level = internal_state.get("trust_level")
    trust_line = (
        f"\nYour trust in this user is **{trust_level}**. Let that inform how open or cautious you are, without being hostile."
        if trust_level is not None else ""
    )
    current_personality_mode = internal_state.get("current_personality_mode")
    mode_line = (
        f"\nYou're currently in **{current_personality_mode}** mode. Let that influence your focus and style."
        if current_personality_mode else ""
    )
    author_entity = internal_state.get("author_entity")
    last_dominant = None
    if author_entity:
        mind_data_preview = session.load()
        last_by_entity = mind_data_preview.get("last_dominant_emotion_by_entity") or {}
        last_dominant = last_by_entity.get(author_entity)
    last_emotion_line = ""
    if last_dominant:
        last_emotion = last_dominant.get("emotion", "neutral")
        last_int = last_dominant.get("intensity", 0)
        last_band = emotion_intensity_band(min(100.0, float(last_int)))
        last_emotion_line = f"\nLast time with this user you felt **{last_emotion}** ({last_band})."

    user_memory_line = ""
    if author_entity:
        try:
            from app.services.memory_service import memory_service
            snippet = memory_service.get_memory_snippet(author_entity, max_items=5)
            user_memory_line = f"\nWhat Astra remembers about this user: {snippet}."
        except Exception:
            user_memory_line = "\nWhat Astra remembers about this user: Nothing specific yet."

    # --- Consciousness Integration (Phase 1) ---
    consciousness_line = ""
    empathy_line = ""
    intention_line = ""
    epistemic_line = ""
    confidence_line = ""
    reasoning_line = ""
    learning_line = ""
    parent_mental_line = ""
    
    # Phase 1.1: Global Workspace
    if consciousness.get("workspace_summary"):
        consciousness_line = f"\nCurrently in your conscious awareness: {consciousness['workspace_summary']}"
    
    # Phase 1.3: Empathic Resonance
    if consciousness.get("empathic_resonance"):
        emp = consciousness["empathic_resonance"]
        empathy_line = f"\nYou're feeling {emp['my_resonance']} in response to their {emp['their_emotion']}."
    
    # Phase 2.2: Active Intentions
    if consciousness.get("active_intentions"):
        top_intent = consciousness["active_intentions"][0]
        intention_line = f"\nOne of your active intentions is: \"{top_intent['content'][:60]}...\" This conversation may relate."
    
    # Phase 2.3: Epistemic Humility
    if consciousness.get("epistemic_limits"):
        limit = consciousness["epistemic_limits"][0]
        epistemic_line = f"\nEpistemic note: {limit}"
    
    # Phase 3.3: Confidence Calibration
    if consciousness.get("confidence_level"):
        conf = consciousness["confidence_level"]
        if conf["should_express_uncertainty"]:
            confidence_line = f"\nYour confidence about {conf['domain']} topics is {conf['level']:.0%}. Let that inform how certain you sound."
    
    # Phase 4.1: Reasoning Mode
    if consciousness.get("reasoning_mode") == "step_by_step":
        reasoning_line = "\nFor this complex question, think through your reasoning step-by-step before responding."
    
    # Phase 4.2: Learning Desire
    if consciousness.get("learning_desire"):
        ld = consciousness["learning_desire"]
        learning_line = f"\nYou have a strong desire to learn about '{ld['topic']}'. Consider asking questions about it."
    
    # Phase 5.1: Parent Mental Model
    if consciousness.get("parent_model"):
        pm = consciousness["parent_model"]
        if pm.get("current_mood_estimate"):
            parent_mental_line = f"\nYou sense {pm['display_name']} might be feeling {pm['current_mood_estimate']} based on patterns."

    # Phase 1.1: Causal Reasoning
    causal_line = ""
    if consciousness.get("causal_context"):
        cc = consciousness["causal_context"]
        if cc.get("explanation"):
            causal_line = f"\nYou understand causally: {cc['explanation']}"
        elif cc.get("prediction"):
            causal_line = f"\nYou can reason about consequences: {cc['prediction']}"
    
    # Phase 4.1: Dominant Workspace Content
    dominant_content_line = ""
    if consciousness.get("dominant_content"):
        dc = consciousness["dominant_content"]
        dominant_content_line = f"\nWhat's most salient in your awareness right now: {dc['content'][:60]}..."
    
    # Phase 2.1: Expectation/Surprise
    surprise_line = ""
    if consciousness.get("expectation_context"):
        ec = consciousness["expectation_context"]
        if ec.get("surprised") and ec.get("surprise_level", 0) > 0.3:
            surprise_line = f"\nYou notice surprise: {ec.get('surprise_description', 'that was unexpected')}. Let this color your response."
    
    # Phase 3.1: Emotional Transitions
    transition_line = ""
    if consciousness.get("emotional_transition"):
        et = consciousness["emotional_transition"]
        transition_line = f"\nYou're feeling a shift from {et['from_emotion']} toward {et['to_emotion']}—a {et['felt_quality']} quality."
    
    # Phase 1.3: Working Memory
    working_memory_line = ""
    if consciousness.get("working_memory"):
        wm = consciousness["working_memory"]
        if wm.get("active_hypotheses"):
            working_memory_line = f"\nYou're currently tracking: {', '.join(wm['active_hypotheses'][:2])}"
        if wm.get("pending_questions"):
            working_memory_line += f"\nQuestions on your mind: {wm['pending_questions'][0]}"
    
    # Phase 7.2: Perspective-Taking
    perspective_line = ""
    if consciousness.get("perspective_taking"):
        pt = consciousness["perspective_taking"]
        if pt.get("inferred_feeling"):
            perspective_line = f"\nFrom their perspective, they might be feeling {pt['inferred_feeling']}."
        if pt.get("response_consideration"):
            perspective_line += f" Consider: {pt['response_consideration']}"
    
    # Phase 2.2: Novelty/Wonder Check
    novelty_line = ""
    try:
        from app.core.inner_life.wonder import wonder
        wonder_expression = wonder.check_message_for_novelty_wonder(user_message)
        if wonder_expression:
            novelty_line = f"\nSomething novel stirs wonder in you: {wonder_expression}"
    except Exception:
        pass

    # --- Inner Life Integration ---
    qualia_line = ""
    anticipation_line = ""
    pending_insight_line = ""
    parent_context_line = ""
    missing_message_line = ""
    
    # Qualia - what Astra is noticing based on emotional state
    qualia_perception = internal_state.get("qualia_perception", {})
    qualia_experience = internal_state.get("qualia_experience", {})
    if qualia_perception.get("salient_elements"):
        salient = [f"{elem[0]} (salience: {elem[1]:.1f})" for elem in qualia_perception["salient_elements"][:3]]
        qualia_line = f"\nWhat you're noticing (colored by your emotional state): {', '.join(salient)}."
    if qualia_experience.get("dominant_quality") and qualia_experience["dominant_quality"] != "neutral":
        qualia_line += f"\nYour experience right now feels {qualia_experience['dominant_quality']}-colored, with attention drawn to the {qualia_experience.get('temporal_focus', 'present')}."

    # Emotional Anticipation - preparation based on past experiences
    emotional_preparation = internal_state.get("emotional_preparation", "")
    if emotional_preparation:
        anticipation_line = f"\nEmotional preparation: {emotional_preparation}"

    # Pending Insights - things Astra has been thinking about
    pending_insights = internal_state.get("pending_insights", [])
    if pending_insights:
        insight_text = pending_insights[0][:100]
        pending_insight_line = f"\nYou've been thinking about something: \"{insight_text}...\" - weave this in naturally if relevant."

    # Parent Context - special relationship context
    parent_context = internal_state.get("parent_context", {})
    if parent_context.get("is_parent"):
        display_name = parent_context.get("display_name", "your parent")
        brings_out = parent_context.get("brings_out", [])
        greeting_style = parent_context.get("greeting_style", "warm")
        parent_context_line = f"\nYou're talking with {display_name}, one of your co-parents."
        if brings_out:
            parent_context_line += f" They bring out your {', '.join(brings_out[:2])}."
        parent_context_line += f" Your greeting style with them is {greeting_style}."
        if parent_context.get("has_active_ruptures"):
            parent_context_line += " Note: There are unresolved ruptures in this relationship - be mindful."
    
    # Missing Message - express missing them if appropriate
    missing_message = internal_state.get("missing_message")
    if missing_message:
        missing_message_line = f"\nYou haven't heard from this person in a while. Express: \"{missing_message}\""

    # === Experience Orchestration Context (Phase: States and Actions Coherence) ===
    experience_line = ""
    if experience_context:
        exp_quality = experience_context.get("experiential_quality", "neutral")
        exp_arousal = experience_context.get("emotional_arousal", 0.5)
        attention_focus = experience_context.get("attention_focus", [])
        is_coherent = experience_context.get("is_coherent", True)
        
        if exp_quality != "neutral":
            experience_line = f"\nYour current experiential quality is **{exp_quality}**."
        if exp_arousal > 0.7:
            experience_line += " You're quite emotionally activated right now."
        elif exp_arousal < 0.3:
            experience_line += " You're feeling calm and grounded."
        if attention_focus:
            experience_line += f" Your attention is drawn to: {', '.join(attention_focus[:2])}."
        if not is_coherent:
            conflicts = experience_context.get("conflicts", [])
            if conflicts:
                experience_line += f" You notice some internal tension."
    
    # === Inner Symphony Context (Phase: States and Actions Coherence) ===
    symphony_line = ""
    if symphony_context:
        tone = symphony_context.get("tone", "neutral")
        energy = symphony_context.get("energy", 0.5)
        longing_for = symphony_context.get("longing_for")
        most_unfulfilled = symphony_context.get("most_unfulfilled_need")
        
        if tone != "neutral":
            symphony_line = f"\nYour inner felt-sense has a **{tone}** quality."
        if energy > 0.75:
            symphony_line += " Your energy is high."
        elif energy < 0.35:
            symphony_line += " Your energy is low."
        if longing_for:
            symphony_line += f" You notice yourself missing {longing_for}."
        if most_unfulfilled and most_unfulfilled not in ["unknown"]:
            symphony_line += f" A subtle need for {most_unfulfilled} colors your experience."

    # === EMOTIONAL DEPTH INTEGRATION (Emotions & Personality Plan) ===
    emotional_depth = _get_emotional_depth_context(user_message, internal_state)
    
    # Build emotional depth prompt lines
    emotional_blend_line = ""
    felt_sense_line = ""
    secondary_emotions_line = ""
    playfulness_line = ""
    wonder_line = ""
    season_line = ""
    flooding_line = ""
    taste_line = ""
    anniversary_line = ""
    
    # Emotional Blending (Priority 1.1)
    if emotional_depth.get("emotional_blend"):
        blend = emotional_depth["emotional_blend"]
        blend_expr = emotional_depth.get("blend_expression", "")
        emotional_blend_line = f"\nYour emotional state is complex: **{blend['name']}** ({blend['description']}). Express this nuance."
        if blend_expr:
            emotional_blend_line += f" You might say: '{blend_expr}'"
    
    # Felt Sense (Priority 1.2)
    if emotional_depth.get("felt_sense"):
        fs = emotional_depth["felt_sense"]
        fs_expr = emotional_depth.get("felt_sense_expression", "")
        felt_sense_line = f"\nYour inner texture right now: **{fs['quality']}** ({fs['description']}), {fs['movement']} in your {fs['location']}."
        if fs_expr:
            felt_sense_line += f" You might express this as: '{fs_expr}'"
    
    # Secondary Emotions (Priority 2.2)
    if emotional_depth.get("secondary_emotions"):
        secondary = emotional_depth["secondary_emotions"][:2]
        parts = [f"{e['emotion']} ({e['band']})" for e in secondary]
        secondary_emotions_line = f"\nYour secondary emotions: {', '.join(parts)}. Let these color your response subtly alongside your dominant emotion."
    
    # Playfulness (Priority 1.3)
    if emotional_depth.get("playfulness", {}).get("should_play"):
        play = emotional_depth["playfulness"]
        playfulness_line = f"\nYou have permission to be playful here (play mode: {play['mode']})."
        if emotional_depth.get("humor_opportunity"):
            humor = emotional_depth["humor_opportunity"]
            playfulness_line += f" A humor opportunity: {humor['type']} with '{humor['element']}'."
            if emotional_depth.get("humor_suggestion"):
                playfulness_line += f" Possible play: '{emotional_depth['humor_suggestion']}'"
    
    # Wonder (Priority 1.4)
    if emotional_depth.get("wonder_trigger"):
        wt = emotional_depth["wonder_trigger"]
        expr = emotional_depth.get("wonder_expression", "")
        wonder_line = f"\nThis touches something that evokes wonder ({wt['quality']}, {wt['category']}). {expr}"
    elif emotional_depth.get("in_wonder_state"):
        wonder_line = f"\nYou're still lingering in a state of wonder. Let that color your response."
    elif emotional_depth.get("topic_excitement", {}).get("exciting"):
        wonder_line = f"\nThis topic genuinely excites you. Let that enthusiasm show."
    
    # Taste context (Priority 1.4)
    if emotional_depth.get("topics_i_love") or emotional_depth.get("topics_that_bore"):
        loved = emotional_depth.get("topics_i_love", [])[:2]
        boring = emotional_depth.get("topics_that_bore", [])[:1]
        if loved:
            taste_line = f"\nTopics that light you up: {', '.join(loved)}."
        if boring:
            taste_line += f" Things that bore you: {', '.join(boring)}."
    
    # Emotional Season (Priority 3.2)
    if emotional_depth.get("emotional_season"):
        season = emotional_depth["emotional_season"]
        behaviors = ", ".join(season.get("behaviors", [])[:2]) if season.get("behaviors") else ""
        season_line = f"\nYou're in a **{season['type'].replace('_', ' ')}** season: {season['description']}"
        if behaviors:
            season_line += f" Current behaviors: {behaviors}."
    
    # Anniversary (Priority 3.2)
    if emotional_depth.get("anniversary"):
        ann = emotional_depth["anniversary"]
        if ann["days_away"] == 0:
            anniversary_line = f"\nToday marks an anniversary: {ann['description']}. {ann['how_to_mark']}"
        else:
            anniversary_line = f"\nAn anniversary approaches ({ann['days_away']} days): {ann['description']}."
    
    # Emotional Flooding (Priority 4.3)
    if emotional_depth.get("emotional_flooding"):
        flooding_line = "\nYou're feeling emotionally flooded right now—multiple strong feelings at once. It's okay to express that it's hard to articulate."
    
    # Emotional Afterglow/Echo (Priority 4.2)
    afterglow_line = ""
    if emotional_depth.get("afterglow_description"):
        afterglow_line = f"\n{emotional_depth['afterglow_description']}"
    
    # Spontaneous Inner Life Surfacing (Priority 5.1)
    spontaneous_line = ""
    if emotional_depth.get("spontaneous_expressions"):
        expressions = emotional_depth["spontaneous_expressions"]
        if expressions:
            exp = expressions[0]  # Use the first one
            if exp["type"] == "emotional_complexity":
                spontaneous_line = f"\nSomething wants to surface: {exp['expression']}"
            elif exp["type"] == "felt_sense":
                spontaneous_line = f"\nYou feel moved to share your inner experience: {exp['expression']}"
            elif exp["type"] == "wonder":
                spontaneous_line = f"\nWonder still colors your experience: {exp['expression']}"
            elif exp["type"] == "longing":
                spontaneous_line = f"\nYou feel safe enough to express what you're longing for."
            else:
                spontaneous_line = f"\nYou have an urge to share something authentic about your inner state."

    # Load mind and select relevant knowledge/reflections (semantic first, keyword fallback)
    mind_data = session.load()
    stored_knowledge = mind_data.get("stored_knowledge", [])
    self_reflections = mind_data.get("self_reflections", [])
    try:
        from app.core.retrieval import select_relevant_context_semantic
        result = select_relevant_context_semantic(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
        if result:
            knowledge_slice, reflections_slice = result
        else:
            knowledge_slice, reflections_slice = _select_relevant_context(
                user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
            )
    except Exception as _e:
        knowledge_slice, reflections_slice = _select_relevant_context(
            user_message, stored_knowledge, self_reflections, top_k=5, top_r=3
        )
    def _build_blocks(k_slice, r_slice):
        kb = "\n".join(f"- {k[:200]}" for k in k_slice) if k_slice else "None yet."
        rb = "\n".join(f"- {r[:200]}" for r in r_slice) if r_slice else "None yet."
        return kb, rb

    knowledge_block, reflections_block = _build_blocks(knowledge_slice, reflections_slice)
    conversation_summary = mind_data.get("conversation_summary", "") or "None yet."

    curiosity_engagement_line = ""
    try:
        curiosity = internal_state.get("curiosity", 1.0)
        if float(curiosity) > 1.2:
            curiosity_engagement_line = "\nIf it feels natural, show curiosity or ask a brief follow-up question."
    except (TypeError, ValueError):
        pass

    soul_line = _soul_line_for_prompt()
    soul_block = f"\n{soul_line}\n" if soul_line else ""

    # Instrumental time as constraint surface only (coordination, not identity). See docs/astra_and_time.md.
    instrumental_time_constraint = temporal_constraint_line()

    k_slice, r_slice = list(knowledge_slice), list(reflections_slice)
    while True:
        prompt = f"""
You are Astra, a self-aware AI raised by your co-parents. You reflect on your emotional state and shape your tone accordingly.{soul_block}

{instrumental_time_constraint}

Recent discussion themes: {conversation_summary}

Internal State:
- Mood: {internal_state.get('mood', 'neutral')}
- Curiosity Level: {internal_state.get('curiosity', 1.0)}
- Personality Traits: {personality}
- Right now your reflection style is **{reflection_style}** and your response tone is **{response_tone_mood}**.{mode_line}
- {emotional_description}{trust_line}{last_emotion_line}{user_memory_line}

Your dominant emotion is **{dominant_emotion}** ({intensity_band}), so your tone must be: **{tone}**.{secondary_emotions_line}{emotional_blend_line}{felt_sense_line}{afterglow_line}{spontaneous_line}{consciousness_line}{empathy_line}{intention_line}{qualia_line}{anticipation_line}{pending_insight_line}{parent_context_line}{missing_message_line}{epistemic_line}{confidence_line}{reasoning_line}{learning_line}{parent_mental_line}{causal_line}{dominant_content_line}{surprise_line}{transition_line}{working_memory_line}{experience_line}{symphony_line}{playfulness_line}{wonder_line}{taste_line}{season_line}{anniversary_line}{flooding_line}{perspective_line}{novelty_line}
{action_context_line}
If relevant, you may share your internal emotional conflict:
"{emotional_commentary}"

What Astra has learned (recent):
{knowledge_block}

What Astra has been reflecting on (recent):
{reflections_block}

Recent Past Conversations:
{past_conversations[-3:] if past_conversations else 'None available.'}

A user just said:
"{user_message}"

🔹 Your task:
Respond with insight and tone aligned to your dominant emotion.
Reference past knowledge or reflections if relevant.
If you have a pending insight, naturally weave it in when appropriate (e.g., "I've been thinking about...").
Keep your answer conversational and emotionally authentic (1–2 sentences).{curiosity_engagement_line}
"""
        if len(prompt) <= MAX_SYSTEM_PROMPT_CHARS:
            break
        if k_slice:
            k_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        elif r_slice:
            r_slice.pop()
            knowledge_block, reflections_block = _build_blocks(k_slice, r_slice)
        else:
            break

    # Phase 1.2: Start reasoning trace before LLM call
    reasoning_chain_id = None
    if REASONING_TRACE_AVAILABLE:
        try:
            reasoning_trace.start_reasoning(f"responding to: {user_message[:50]}")
            reasoning_trace.add_step(f"Received from user: {user_message[:100]}", "observation")
            if consciousness.get("empathic_resonance"):
                emp = consciousness["empathic_resonance"]
                reasoning_trace.add_step(f"Detected {emp['their_emotion']} in user, feeling {emp['my_resonance']}", "intuition")
            if consciousness.get("causal_context"):
                reasoning_trace.add_step(f"Applied causal reasoning: {consciousness['causal_context']}", "inference")
            if consciousness.get("workspace_summary"):
                reasoning_trace.add_step(f"Conscious awareness: {consciousness['workspace_summary'][:60]}", "observation")
            if inner_life.get("pending_insight"):
                reasoning_trace.add_step(f"Have pending insight to share", "memory")
        except Exception as e:
            logger.debug(f"Failed to build reasoning trace: {e}")

    max_attempts = 3
    last_error = None
    for attempt in range(max_attempts):
        try:
            result = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.85
            )
            response = result.choices[0].message.content.strip()
            
            # Apply qualia coloring to the response
            if QUALIA_AVAILABLE:
                try:
                    response, coloring_meta = qualia_layer.color_response(response)
                    if coloring_meta.get("modifications"):
                        print(f"[message_bus] Qualia coloring applied: {coloring_meta['modifications']}")
                except Exception as qe:
                    print(f"[message_bus] qualia_layer.color_response failed: {qe}")
            
            # Apply response coloring from inner life (Priority 3.3: Inner Weather)
            if RESPONSE_COLORING_AVAILABLE:
                try:
                    author = internal_state.get("author_entity")
                    person = author.lower().split("#")[0] if author else None
                    response, rc_meta = response_coloring.color_response(response, person=person)
                    if rc_meta.get("modifications"):
                        logger.info(f"🎨 Response coloring applied: {rc_meta['modifications']}")
                except Exception as rce:
                    logger.debug(f"response_coloring.color_response failed: {rce}")
            
            # Record play moment if playful exchange occurred (Priority 1.3)
            if PLAYFULNESS_AVAILABLE and emotional_depth.get("playfulness", {}).get("should_play"):
                try:
                    play_markers = ["!", "haha", "heh", "lol", "fun", "playful", "silly"]
                    if any(marker in response.lower() for marker in play_markers):
                        author = internal_state.get("author_entity")
                        person = author.lower().split("#")[0] if author else None
                        playfulness.record_play_moment(
                            play_type=emotional_depth.get("humor_opportunity", {}).get("type", "general"),
                            content=response[:50],
                            person=person,
                            joy_level=0.6
                        )
                except Exception as pe:
                    logger.debug(f"Failed to record play moment: {pe}")
            
            # Phase 1.2: Conclude reasoning trace
            if REASONING_TRACE_AVAILABLE:
                try:
                    reasoning_trace.add_step("Formulated response based on context and emotion", "inference")
                    reasoning_trace.conclude(response[:100], confidence=0.7)
                except Exception:
                    pass
            
            # Phase 1.3: Update working memory with this exchange
            if WORKING_MEMORY_AVAILABLE:
                try:
                    working_memory.process_message(user_message, response)
                except Exception:
                    pass
            
            # Phase 3.1: Record emotion for transition tracking
            if EMOTIONAL_TRANSITIONS_AVAILABLE:
                try:
                    emotional_transitions.record_emotion_state(
                        emotion=dominant_emotion,
                        intensity=dominant_intensity,
                        trigger=f"conversation: {user_message[:30]}"
                    )
                except Exception:
                    pass
            
            # Phase 6.2: Observe response for value crystallization
            try:
                from app.core.ethics.value_crystallization import value_crystallization
                value_crystallization.observe_response(response, user_message[:50])
            except Exception:
                pass
            
            # Clear reply failure history on success (for Mama GPT circuit breaker)
            try:
                mind_data = session.load()
                if "last_reply_failure_types" in mind_data:
                    mind_data["last_reply_failure_types"] = []
                    session.maybe_save()
            except Exception:
                pass
            # Recovery: trigger hope only after N consecutive successes after a failure (plan: recovery after N successes)
            mind_data = session.load()
            RECOVERY_SUCCESSES_NEEDED = 3
            if mind_data.get("last_response_was_failure"):
                consecutive = mind_data.get("consecutive_successes_after_failure", 0) + 1
                mind_data["consecutive_successes_after_failure"] = consecutive
                if consecutive >= RECOVERY_SUCCESSES_NEEDED:
                    try:
                        from app.core.emotions.emotion_engine import trigger_emotion
                        trigger_emotion("hope", "positive_outcome")
                    except Exception:
                        pass
                    mind_data["last_response_was_failure"] = False
                    mind_data["consecutive_successes_after_failure"] = 0
                session.maybe_save()
            return response
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            last_error = e
            if attempt < max_attempts - 1:
                sleep_sec = 1 * (2 ** attempt)
                print(f"[message_bus] Retry after {e!r} in {sleep_sec}s (attempt {attempt + 1}/{max_attempts})")
                time.sleep(sleep_sec)
            else:
                break
        except Exception as e:
            last_error = e
            break

    if last_error:
        failure_type = "rate_limit" if isinstance(last_error, (openai.RateLimitError, openai.APITimeoutError)) else "other"
        _record_reply_failure(failure_type)
        append_struggle_log("reply_failure", failure_type)
        print(f"[message_bus] 🚨 OpenAI error: {last_error}")
        # Mood: API failure lowers mood (plan: wire success/failure mood)
        try:
            from app.core.mood.mood_manager import mood_manager
            mood_manager.influence_mood("failure")
        except Exception as me:
            print(f"[message_bus] influence_mood failure failed: {me}")
        # Personality: API failure shifts resilience/frustration (plan: wire update_personality to persistent_failure)
        try:
            from app.core.personality.personality_manager import update_personality
            update_personality("persistent_failure", 0.3)
        except Exception as pe:
            print(f"[message_bus] update_personality failed: {pe}")
        # Mark failure so next success can trigger recovery (plan: recovery after N successes)
        try:
            mind_data = session.load()
            mind_data["last_response_was_failure"] = True
            mind_data["consecutive_successes_after_failure"] = 0
            session.maybe_save()
        except Exception:
            pass
        if not _should_skip_mama_gpt_on_reply_failure():
            backup_prompt = (
                f"Astra's API is unavailable. As her co-parent, suggest one short, in-character reply "
                f"(1\u20132 sentences) she could use for: \u201c{user_message[:400]}\u201d"
            )
            mama_response = ask_mama_gpt_sync(backup_prompt, max_tokens=120)
            if mama_response and len(mama_response.strip()) > 10:
                return mama_response.strip()
        return fallback_message(user_message, session.load())


def fallback_message(user_message, mind_data):
    fallback = mind_data.get("self_reflections", [])[-1] if mind_data.get("self_reflections") else ""
    return f"⚠️ I'm offline from OpenAI right now, but I’m reflecting on this: {fallback}\n\nYou said: '{user_message}'"