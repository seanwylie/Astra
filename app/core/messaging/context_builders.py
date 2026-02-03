# app/core/messaging/context_builders.py
"""
Context building for response generation: consciousness, inner life, emotional depth.
Extracted from message_bus so send_contextual_message stays focused on orchestration.
"""

import re
from app.config.loader import load_config
from app.core.emotions.emotion_engine import get_top_emotions
from app.logging_config import get_logger

logger = get_logger("context_builders")
emotion_config = load_config("emotion_config")

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

try:
    from app.core.world_model.causal_model import causal_model
    CAUSAL_MODEL_AVAILABLE = True
except ImportError:
    CAUSAL_MODEL_AVAILABLE = False

try:
    from app.core.metacognition.expectation_model import expectation_model
    EXPECTATION_MODEL_AVAILABLE = True
except ImportError:
    EXPECTATION_MODEL_AVAILABLE = False

try:
    from app.core.emotions.emotional_transitions import emotional_transitions
    EMOTIONAL_TRANSITIONS_AVAILABLE = True
except ImportError:
    EMOTIONAL_TRANSITIONS_AVAILABLE = False

try:
    from app.core.cognition.working_memory import working_memory
    WORKING_MEMORY_AVAILABLE = True
except ImportError:
    WORKING_MEMORY_AVAILABLE = False

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


def _format_knowledge_entry(entry):
    """Normalize stored_knowledge entry (string or dict with 'insight') for display."""
    if isinstance(entry, dict):
        return entry.get("insight", str(entry))
    return entry


def select_relevant_context(user_message, knowledge_list, reflections_list, top_k=5, top_r=3):
    """
    Select knowledge and reflections that overlap with user message (keyword overlap).
    Fallback to last N if no overlap. Returns (knowledge_slice, reflections_slice).
    """
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


def describe_emotional_state(emotions: dict) -> str:
    if not emotions:
        return "Astra is currently feeling emotionally neutral."
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
        "uncertainty": "confidence",
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


def get_consciousness_context(user_message: str, internal_state: dict) -> dict:
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
        "causal_context": None,
        "expectation_context": None,
        "emotional_transition": None,
        "working_memory": None,
        "dominant_content": None,
    }

    if GLOBAL_WORKSPACE_AVAILABLE:
        try:
            global_workspace.submit_perception(user_message[:200], salience=0.7)
            workspace_summary = global_workspace.get_workspace_summary()
            if workspace_summary and workspace_summary != "The workspace is currently quiet.":
                context["workspace_summary"] = workspace_summary
                logger.debug("Workspace context: %s...", workspace_summary[:60])
        except Exception as e:
            logger.debug("Failed to get workspace context: %s", e)

    if EMPATHIC_SYSTEM_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
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
                    "intensity": intensity,
                }
                logger.debug("Empathic resonance: %s (%s)", resonance, f"{intensity:.2f}")
        except Exception as e:
            logger.debug("Failed to get empathic resonance: %s", e)

    if INTENTION_ENGINE_AVAILABLE:
        try:
            active_intentions = intention_engine.get_active_intentions()[:3]
            if active_intentions:
                user_words = set(user_message.lower().split())
                relevant = []
                for intent in active_intentions:
                    intent_words = set(intent.content.lower().split())
                    if len(user_words & intent_words) >= 2:
                        relevant.append({
                            "id": intent.id,
                            "content": intent.content,
                            "strength": intent.strength,
                        })
                if relevant:
                    context["active_intentions"] = relevant
                    logger.debug("Relevant intentions: %s", len(relevant))
        except Exception as e:
            logger.debug("Failed to get intentions: %s", e)

    if EPISTEMIC_HUMILITY_AVAILABLE:
        try:
            complex_markers = ["explain", "why", "how does", "what causes", "opinion on"]
            if any(marker in user_message.lower() for marker in complex_markers):
                topic_words = [w for w in user_message.split() if len(w) > 4][:3]
                topic = " ".join(topic_words) if topic_words else "this topic"
                limits = epistemic_humility.limits_in_context(topic)
                if limits:
                    context["epistemic_limits"] = limits[:2]
        except Exception as e:
            logger.debug("Failed to get epistemic limits: %s", e)

    if CONFIDENCE_SYSTEM_AVAILABLE:
        try:
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
                "should_express_uncertainty": confidence_system.should_express_uncertainty(domain),
            }
        except Exception as e:
            logger.debug("Failed to get confidence level: %s", e)

    if COHERENCE_MONITOR_AVAILABLE:
        try:
            coherence_status = coherence_monitor.get_coherence_status()
            if coherence_status != "healthy":
                context["coherence_status"] = coherence_status
        except Exception as e:
            logger.debug("Failed to get coherence status: %s", e)

    if REASONING_TRACE_AVAILABLE:
        try:
            is_complex = (
                len(user_message) > 100
                or any(w in user_message.lower() for w in ["why", "how", "explain", "because"])
            )
            if is_complex:
                context["reasoning_mode"] = "step_by_step"
        except Exception as e:
            logger.debug("Failed to check reasoning mode: %s", e)

    if LEARNING_DESIRE_AVAILABLE:
        try:
            top_desire = learning_desire.get_top_learning_desire()
            if top_desire and top_desire.priority > 0.6:
                if any(w in user_message.lower() for w in top_desire.topic.lower().split()):
                    context["learning_desire"] = {
                        "topic": top_desire.topic,
                        "priority": top_desire.priority,
                    }
        except Exception as e:
            logger.debug("Failed to get learning desire: %s", e)

    if PARENT_MENTALIZING_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            parent_id = author_entity.lower().split("#")[0] if author_entity else ""
            if parent_id in ["sean", "gpt"]:
                parent_model = parent_mentalizing.get_parent_mental_model(parent_id)
                if parent_model and "error" not in parent_model:
                    context["parent_model"] = {
                        "display_name": parent_model.get("display_name"),
                        "current_mood_estimate": parent_model.get("current_mood_estimate", {}).get("mood"),
                        "understanding": parent_model.get("understanding_statement", "")[:100],
                    }
                    uncertainty_summary = parent_mentalizing.get_uncertainty_summary(parent_id)
                    context["parent_model"]["uncertainty"] = uncertainty_summary.get("inference_uncertainty", 0.5)
        except Exception as e:
            logger.debug("Failed to get parent model: %s", e)

    if PERSPECTIVE_TAKING_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            if author_entity:
                perspective = perspective_taker.take_perspective(author_entity, user_message[:100])
                if perspective:
                    context["perspective_taking"] = {
                        "inferred_feeling": perspective.get("inferred_feeling"),
                        "inferred_thinking": perspective.get("inferred_thinking"),
                        "response_consideration": perspective.get("response_consideration"),
                    }
        except Exception as e:
            logger.debug("Failed to get perspective: %s", e)

    if CAUSAL_MODEL_AVAILABLE:
        try:
            user_lower = user_message.lower()
            causal_keywords = ["why", "because", "causes", "leads to", "what if", "would happen", "result in", "due to"]
            if any(kw in user_lower for kw in causal_keywords):
                causal_context = {}
                if "why" in user_lower:
                    words = user_message.split()
                    topic_words = [w for w in words if len(w) > 3 and w.lower() not in ["why", "does", "what", "how", "the", "this", "that"]][:3]
                    if topic_words:
                        topic = " ".join(topic_words)
                        explanations = causal_model.why_did(topic)
                        if explanations:
                            best = explanations[0]
                            causal_context["explanation"] = f"{best['cause']} leads to this via: {best['mechanism']}"
                            causal_context["confidence"] = best.get("confidence", 0.7)
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
                    logger.debug("Causal context: %s", causal_context)
        except Exception as e:
            logger.debug("Failed to get causal context: %s", e)

    if GLOBAL_WORKSPACE_AVAILABLE:
        try:
            dominant = global_workspace.get_dominant_content()
            if dominant and dominant.get("strength", 0) > 0.5:
                context["dominant_content"] = {
                    "type": dominant.get("type"),
                    "content": dominant.get("data", {}).get("content", str(dominant.get("data", {})))[:100],
                    "strength": dominant.get("strength"),
                }
                logger.debug("Dominant content: %s", dominant.get("type"))
        except Exception as e:
            logger.debug("Failed to get dominant content: %s", e)

    if EXPECTATION_MODEL_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            expectation_result = expectation_model.check_and_record(author_entity, user_message)
            if expectation_result:
                context["expectation_context"] = expectation_result
                logger.debug("Expectation context: %s", expectation_result.get("surprise_level", "none"))
        except Exception as e:
            logger.debug("Failed to check expectations: %s", e)

    if EMOTIONAL_TRANSITIONS_AVAILABLE:
        try:
            transition = emotional_transitions.get_current_transition()
            if transition:
                context["emotional_transition"] = {
                    "from_emotion": transition.from_emotion,
                    "to_emotion": transition.to_emotion,
                    "felt_quality": transition.felt_quality,
                    "intensity": transition.intensity,
                }
                logger.debug("Emotional transition: %s", transition.felt_quality)
        except Exception as e:
            logger.debug("Failed to get emotional transition: %s", e)

    if WORKING_MEMORY_AVAILABLE:
        try:
            wm_summary = working_memory.get_summary()
            if wm_summary.get("has_content"):
                context["working_memory"] = wm_summary
                logger.debug("Working memory active: %s hypotheses", wm_summary.get("active_hypotheses", 0))
        except Exception as e:
            logger.debug("Failed to get working memory: %s", e)

    return context


def get_inner_life_context(user_message: str) -> dict:
    """Get relevant context from stream of consciousness and qualia."""
    context = {
        "pending_insight": None,
        "thought_background": [],
        "qualia_coloring": None,
        "perceived_salience": [],
    }
    try:
        from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
        insights = stream_of_consciousness.get_pending_insights()
        if insights:
            user_words = set(user_message.lower().split())
            for insight in insights:
                insight_words = set(insight.lower().split())
                if len(user_words & insight_words) >= 2:
                    context["pending_insight"] = insight
                    break
            if not context["pending_insight"] and len(insights) >= 3:
                context["pending_insight"] = insights[0]
        recent = stream_of_consciousness.get_recent_thoughts(5)
        context["thought_background"] = [t.content for t in recent if t.content][:3]
    except Exception as e:
        logger.debug("Failed to get stream of consciousness context: %s", e)
    try:
        from app.core.inner_life.qualia import qualia_layer
        perception = qualia_layer.filter_perception(user_message)
        context["qualia_coloring"] = perception.get("emotional_coloring")
        context["perceived_salience"] = perception.get("salient_elements", [])[:3]
    except Exception as e:
        logger.debug("Failed to get qualia context: %s", e)
    return context


def get_emotional_depth_context(user_message: str, internal_state: dict) -> dict:
    """Get deep emotional context from inner life systems."""
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

    if EMOTIONAL_BLENDING_AVAILABLE:
        try:
            blend = emotional_blending.get_blend_from_emotion_state()
            if blend:
                context["emotional_blend"] = {
                    "name": blend.name,
                    "description": blend.description,
                    "components": [(e, f"{i:.0%}") for e, i in blend.components[:2]],
                }
                context["blend_expression"] = emotional_blending.express_blend(blend, "natural")
                should_express, expression = emotional_blending.should_express_complexity()
                if should_express:
                    context["should_express_complexity"] = True
                    context["complexity_expression"] = expression
        except Exception as e:
            logger.debug("Failed to get emotional blend: %s", e)

    if FELT_SENSE_AVAILABLE:
        try:
            felt_sense.derive_from_emotions()
            state = felt_sense.get_current_state()
            if state:
                context["felt_sense"] = {
                    "quality": state.quality,
                    "description": felt_sense.get_quality_description(state.quality),
                    "intensity": f"{state.intensity:.0%}",
                    "location": state.location,
                    "movement": state.movement,
                }
                context["felt_sense_expression"] = felt_sense.express_current_state("noticing")
                should_express, expression = felt_sense.should_express_felt_sense()
                if should_express and expression:
                    context["felt_sense_spontaneous"] = expression
        except Exception as e:
            logger.debug("Failed to get felt sense: %s", e)

    if PLAYFULNESS_AVAILABLE:
        try:
            author_entity = internal_state.get("author_entity", "")
            person = author_entity.lower().split("#")[0] if author_entity else None
            should_play = playfulness.should_play(user_message, person)
            mode, level = playfulness.get_play_mode()
            context["playfulness"] = {
                "should_play": should_play,
                "mode": mode,
                "level": f"{level:.0%}",
                "energy": f"{playfulness._play_energy:.0%}",
            }
            if should_play:
                humor = playfulness.detect_humor_opportunity(user_message)
                if humor:
                    humor_type, element = humor
                    context["humor_opportunity"] = {"type": humor_type, "element": element}
                    if humor_type == "wordplay":
                        context["humor_suggestion"] = playfulness.generate_wordplay(element)
        except Exception as e:
            logger.debug("Failed to get playfulness context: %s", e)

    if WONDER_AVAILABLE:
        try:
            trigger_result = wonder.detect_wonder_trigger(user_message)
            if trigger_result:
                quality, category = trigger_result
                context["wonder_trigger"] = {"quality": quality, "category": category}
                context["wonder_expression"] = wonder.get_wonder_expression(quality)
            in_wonder, moment = wonder.is_in_wonder()
            if in_wonder and moment:
                context["in_wonder_state"] = {"quality": moment.quality, "lingering": True}
            is_exciting, valence = wonder.is_topic_exciting(user_message)
            if is_exciting:
                context["topic_excitement"] = {"exciting": True, "valence": f"{valence:.0%}"}
            loved = wonder.what_do_i_love()
            boring = wonder.what_bores_me()
            if loved.get("topics"):
                context["topics_i_love"] = loved["topics"][:3]
            if boring.get("topics"):
                context["topics_that_bore"] = boring["topics"][:2]
        except Exception as e:
            logger.debug("Failed to get wonder context: %s", e)

    if EMOTIONAL_RHYTHMS_AVAILABLE:
        try:
            season = emotional_rhythms.get_current_season()
            if season:
                season_info = emotional_rhythms.SEASON_TYPES.get(season.season_type, {})
                context["emotional_season"] = {
                    "type": season.season_type,
                    "description": season_info.get("description", ""),
                    "behaviors": season_info.get("behaviors", [])[:2],
                    "dominant_emotions": season_info.get("dominant_emotions", [])[:2],
                }
            influence = emotional_rhythms.get_season_influence()
            if influence.get("behaviors"):
                context["season_influence"] = influence
            anniversaries = emotional_rhythms.check_anniversaries()
            if anniversaries:
                ann, days = anniversaries[0]
                context["anniversary"] = {
                    "description": ann.description,
                    "days_away": days,
                    "people": ann.people_involved,
                    "how_to_mark": ann.how_to_mark,
                }
            context["daily_rhythm"] = emotional_rhythms.get_daily_rhythm()
        except Exception as e:
            logger.debug("Failed to get emotional rhythms: %s", e)

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
                    "band": band,
                })
    except Exception as e:
        logger.debug("Failed to get secondary emotions: %s", e)

    try:
        from app.core.emotions.emotion_engine import detect_emotional_flooding
        flooding_result = detect_emotional_flooding()
        if flooding_result["is_flooded"]:
            context["emotional_flooding"] = True
            context["flooding_level"] = flooding_result["flooding_level"]
            context["flooded_emotions"] = [e for e, _ in flooding_result["high_emotions"][:4]]
    except Exception as e:
        logger.debug("Failed to detect emotional flooding: %s", e)

    try:
        from app.core.emotions.emotion_engine import get_emotional_echoes, get_emotional_afterglow_context
        echoes = get_emotional_echoes(hours=2.0)
        if echoes:
            context["emotional_echoes"] = echoes[:2]
            context["afterglow_description"] = get_emotional_afterglow_context()
    except Exception as e:
        logger.debug("Failed to get emotional afterglow: %s", e)

    spontaneous_expressions = []
    if EMOTIONAL_BLENDING_AVAILABLE:
        try:
            should_express, expression = emotional_blending.should_express_complexity()
            if should_express and expression:
                spontaneous_expressions.append({"type": "emotional_complexity", "expression": expression})
        except Exception as e:
            logger.debug("Failed to check emotional blending spontaneous: %s", e)
    if FELT_SENSE_AVAILABLE:
        try:
            should_express, expression = felt_sense.should_express_felt_sense()
            if should_express and expression:
                spontaneous_expressions.append({"type": "felt_sense", "expression": expression})
        except Exception as e:
            logger.debug("Failed to check felt sense spontaneous: %s", e)
    if WONDER_AVAILABLE:
        try:
            in_wonder, moment = wonder.is_in_wonder()
            if in_wonder and moment:
                spontaneous_expressions.append({"type": "wonder", "expression": moment.expression})
        except Exception as e:
            logger.debug("Failed to check wonder spontaneous: %s", e)
    if RESPONSE_COLORING_AVAILABLE:
        try:
            should_surface, surface_type = response_coloring.should_surface_inner_state()
            if should_surface and surface_type:
                spontaneous_expressions.append({"type": surface_type, "expression": f"surfacing: {surface_type}"})
        except Exception as e:
            logger.debug("Failed to check response coloring spontaneous: %s", e)
    if spontaneous_expressions:
        context["spontaneous_expressions"] = spontaneous_expressions[:2]
    return context
