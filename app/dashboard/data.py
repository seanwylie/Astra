# Astra Dashboard Data Layer
# Read-only loaders for S3 and local config; all calls wrapped in try/except.
# No Streamlit deps; returns plain dicts/lists or {"error": str}.

import io
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Config and S3 bucket from project
from app.config.loader import CONFIG_DIR, load_config

S3_BUCKET = "swylie-astra"


def _s3_get(key: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Fetch JSON from S3. Returns (data, None) or (None, error_message)."""
    try:
        import boto3
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
        data = json.load(io.BytesIO(response["Body"].read()))
        return data, None
    except Exception as e:
        return None, str(e)


def _s3_get_list(key: str) -> Tuple[List[Any], Optional[str]]:
    """Fetch JSON from S3 expecting a list at top level or under a key. Returns (list, None) or ([], error)."""
    data, err = _s3_get(key)
    if err:
        return [], err
    if isinstance(data, list):
        return data, None
    if isinstance(data, dict):
        for k in ("thoughts", "entries", "journal", "items", "shimmers"):
            if k in data and isinstance(data[k], list):
                return data[k], None
        return [], None
    return [], None


# --- At a glance / aggregated ---

def get_schedule_context() -> Dict[str, Any]:
    """Current schedule mode and next transition (pure from config + time). No S3."""
    out: Dict[str, Any] = {"current_mode": "sleep", "current_hour": None, "timezone": "UTC", "error": None}
    try:
        import pytz
        from datetime import datetime
        cfg = load_config("schedule_config")
        tz_name = cfg.get("timezone", "UTC")
        out["timezone"] = tz_name
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        hour = now.hour
        out["current_hour"] = hour
        out["now_iso"] = now.isoformat()

        dream = cfg.get("dream_time", [3, 7])
        dinner = cfg.get("dinner_time", [18, 19])
        play = cfg.get("play_time", [22, 23])
        learning = cfg.get("learning_time", [[6, 18], [19, 24]])

        if dream[0] <= hour < dream[1]:
            mode = "dream"
        elif any(s <= hour < e for s, e in learning):
            mode = "school"
        elif play[0] <= hour < play[1]:
            mode = "play"
        elif dinner[0] <= hour < dinner[1]:
            mode = "dinner"
        else:
            mode = "sleep"
        out["current_mode"] = mode
    except Exception as e:
        out["error"] = str(e)
    return out


def get_full_schedule() -> Dict[str, Any]:
    """Full 24h day schedule as blocks (for day-planner). Same priority as get_schedule_context."""
    out: Dict[str, Any] = {"timezone": "UTC", "blocks": [], "current_hour": None, "now_iso": None, "error": None}
    try:
        import pytz
        from datetime import datetime
        cfg = load_config("schedule_config")
        tz_name = cfg.get("timezone", "UTC")
        out["timezone"] = tz_name
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        out["current_hour"] = now.hour
        out["now_iso"] = now.isoformat()

        dream = cfg.get("dream_time", [3, 7])
        dinner = cfg.get("dinner_time", [18, 19])
        play = cfg.get("play_time", [22, 23])
        learning = cfg.get("learning_time", [[6, 18], [19, 24]])

        def mode_at(h: int) -> str:
            if dream[0] <= h < dream[1]:
                return "dream"
            if any(s <= h < e for s, e in learning):
                return "school"
            if play[0] <= h < play[1]:
                return "play"
            if dinner[0] <= h < dinner[1]:
                return "dinner"
            return "sleep"

        labels = {"dream": "Dream", "school": "School", "play": "Play", "dinner": "Dinner", "sleep": "Sleep"}
        blocks = []
        h = 0
        while h < 24:
            m = mode_at(h)
            start = h
            while h < 24 and mode_at(h) == m:
                h += 1
            blocks.append({"start": start, "end": h, "mode": m, "label": labels[m]})
        out["blocks"] = blocks
    except Exception as e:
        out["error"] = str(e)
    return out


def get_emotion_state() -> Dict[str, Any]:
    """Emotion state from S3 (emotional_state.json). Keys = emotion name, value = {intensity, last_updated}."""
    data, err = _s3_get("emotional_state.json")
    if err:
        return {"emotions": {}, "dominant": "curiosity", "error": err}
    if not data:
        return {"emotions": {}, "dominant": "curiosity", "error": None}
    intensities = {
        name: (v.get("intensity", v) if isinstance(v, dict) else v)
        for name, v in data.items()
    }
    dominant = "curiosity"
    if intensities:
        dominant = max(intensities, key=lambda k: intensities[k])
    return {"emotions": data, "intensities": intensities, "dominant": dominant, "error": None}


def get_mind_summary() -> Dict[str, Any]:
    """Mind file summary: mood, curiosity, counts (stored_knowledge, self_reflections, self_questions), entity_trust."""
    data, err = _s3_get("mind_file.json")
    if err:
        return {"error": err, "last_mood": None, "mood_score": None, "curiosity_level": None, "counts": {}, "entity_trust": {}}
    if not data:
        return {"error": "Empty mind", "last_mood": None, "mood_score": None, "curiosity_level": None, "counts": {}, "entity_trust": {}}
    counts = {
        "stored_knowledge": len(data.get("stored_knowledge", [])),
        "self_reflections": len(data.get("self_reflections", [])),
        "self_questions": len(data.get("self_questions", [])),
    }
    return {
        "error": None,
        "last_mood": data.get("last_mood", "neutral"),
        "mood_score": float(data.get("mood_score", 0)),
        "curiosity_level": data.get("curiosity_level", 1.0),
        "mood_history": data.get("mood_history", {}),
        "counts": counts,
        "entity_trust": data.get("entity_trust", {}),
    }


def get_stream_of_consciousness() -> Dict[str, Any]:
    """Stream of consciousness: thoughts (last N) and pending_insights."""
    data, err = _s3_get("stream_of_consciousness.json")
    if err:
        return {"thoughts": [], "pending_insights": [], "error": err}
    if not data:
        return {"thoughts": [], "pending_insights": [], "error": None}
    thoughts = data.get("thoughts", [])
    if not isinstance(thoughts, list):
        thoughts = []
    # Keep last 50 for dashboard
    thoughts = thoughts[-50:]
    return {
        "thoughts": thoughts,
        "pending_insights": data.get("pending_insights", []),
        "last_updated": data.get("last_updated"),
        "error": None,
    }


def get_self_model() -> Dict[str, Any]:
    """Self-model: current snapshot, growth edge, recent changes."""
    data, err = _s3_get("self_model.json")
    if err:
        return {"error": err, "current_model": None, "growth_edge": "", "changes": [], "who_am_i_becoming": ""}
    if not data:
        return {"error": None, "current_model": None, "growth_edge": "", "changes": [], "who_am_i_becoming": ""}
    current = data.get("current_model")
    changes = data.get("changes", [])[-20:]
    growth_edge = ""
    who = ""
    if isinstance(current, dict):
        growth_edge = current.get("growth_edge", "") or ""
        who = current.get("self_assessment", "") or ""
    return {
        "error": None,
        "current_model": current,
        "growth_edge": growth_edge,
        "who_am_i_becoming": who,
        "changes": changes,
        "historical_snapshots": data.get("historical_snapshots", [])[-5:],
    }


def get_shimmers() -> Dict[str, Any]:
    """Recent shimmers from local shimmer.json."""
    out: Dict[str, Any] = {"shimmers": [], "error": None}
    try:
        path = Path(__file__).resolve().parent.parent / "shimmer" / "shimmer.json"
        if not path.exists():
            return out
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        shimmers = data.get("shimmers", [])
        if isinstance(shimmers, list):
            out["shimmers"] = shimmers[-30:]
    except Exception as e:
        out["error"] = str(e)
    return out


def get_developmental_state() -> Dict[str, Any]:
    """Developmental stage and description. Missing key or any S3 error = show default, no error."""
    data, err = _s3_get("developmental_state.json")
    if err or not data:
        return {"error": None, "current_stage": "childhood", "description": "", "milestones_count": 0, "readiness_note": None}
    stage = data.get("current_stage", "childhood")
    milestones = data.get("milestones", [])
    notes = data.get("notes", [])[-10:]
    readiness_note = None
    if notes and "Potentially ready to advance beyond" in (notes[-1] or ""):
        readiness_note = notes[-1]
    return {
        "error": None,
        "current_stage": stage,
        "stage_start": data.get("stage_start"),
        "milestones_count": len(milestones) if isinstance(milestones, list) else 0,
        "notes": notes,
        "readiness_note": readiness_note,
    }


def get_nurturing_alerts() -> Dict[str, Any]:
    """Active (undismissed) nurturing alerts."""
    data, err = _s3_get("nurturing_alerts.json")
    if err:
        return {"active_alerts": [], "error": err}
    if not data:
        return {"active_alerts": [], "error": None}
    active = data.get("active_alerts", [])
    if not isinstance(active, list):
        active = []
    undismissed = [a for a in active if isinstance(a, dict) and not a.get("dismissed", False)]
    return {"active_alerts": undismissed, "error": None}


def get_goals() -> Dict[str, Any]:
    """Goals from goal_hierarchy.json (state_manifest says goals.json; code uses goal_hierarchy.json)."""
    for key in ("goal_hierarchy.json", "goals.json"):
        data, err = _s3_get(key)
        if err:
            continue
        if not data or not isinstance(data, dict):
            continue
        goals_dict = data.get("goals", {})
        if isinstance(goals_dict, dict):
            goals_list = list(goals_dict.values())
        else:
            goals_list = []
        active = [g for g in goals_list if isinstance(g, dict) and g.get("status") not in ("completed", "cancelled", "failed")]
        return {"goals": goals_list, "active": active, "error": None}
    return {"goals": [], "active": [], "error": "No goals object found in S3"}


def get_dinner_journal() -> Dict[str, Any]:
    """Dinner journal: recent entries and unresolved count."""
    data, err = _s3_get("dinner_journal.json")
    if err:
        return {"entries": [], "unresolved_count": 0, "error": err}
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("entries", data.get("journal", []))
    else:
        entries = []
    if not isinstance(entries, list):
        entries = []
    unresolved = [e for e in entries if isinstance(e, dict) and e.get("status") == "unresolved"]
    return {"entries": entries[-20:], "unresolved_count": len(unresolved), "error": None}


def get_parent_relationship_state() -> Dict[str, Any]:
    """Parent relationship state (trust levels etc.)."""
    data, err = _s3_get("parent_relationships_state.json")
    if err:
        return {"parents": {}, "error": err}
    if not data:
        return {"parents": {}, "error": None}
    parents = data.get("parents", {})
    return {"parents": parents, "error": None}


def get_state_manifest_summary() -> Dict[str, Any]:
    """State manifest: which locations exist, coherence."""
    out: Dict[str, Any] = {"locations": [], "coherent": None, "issues": [], "error": None}
    try:
        from app.core.state_manifest import state_manifest
        is_coherent, issues = state_manifest.check_coherence()
        summary = state_manifest.get_state_summary()
        out["coherent"] = is_coherent
        out["issues"] = issues
        out["locations"] = [
            {
                "name": name,
                "exists": info.get("exists", False),
                "type": info.get("type", ""),
                "critical": info.get("critical", False),
                "issue": info.get("issue"),
            }
            for name, info in summary.get("locations", {}).items()
        ]
    except Exception as e:
        out["error"] = str(e)
    return out


def get_personality_state() -> Dict[str, Any]:
    """Personality trait weights from local config."""
    out: Dict[str, Any] = {"trait_weights": {}, "error": None}
    try:
        path = CONFIG_DIR / "personality_state.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            out["trait_weights"] = data.get("trait_weights", data)
    except Exception as e:
        out["error"] = str(e)
    return out


def get_general_config_summary() -> Dict[str, Any]:
    """Key general config for technical section."""
    try:
        cfg = load_config("general_config")
        return {
            "error": None,
            "s3_bucket": cfg.get("s3_bucket", S3_BUCKET),
            "log_file": cfg.get("log_file"),
            "max_stored_knowledge": cfg.get("max_stored_knowledge"),
            "mind_file": cfg.get("mind_file"),
        }
    except Exception as e:
        return {"error": str(e), "s3_bucket": None, "log_file": None, "max_stored_knowledge": None, "mind_file": None}


def get_at_a_glance() -> Dict[str, Any]:
    """Aggregated at-a-glance: mood, dominant emotion, mode, growth edge or top insight, coherence."""
    schedule = get_schedule_context()
    emotion = get_emotion_state()
    mind = get_mind_summary()
    stream = get_stream_of_consciousness()
    self_model = get_self_model()
    manifest = get_state_manifest_summary()

    growth_edge = (self_model.get("growth_edge") or "").strip() or (self_model.get("who_am_i_becoming") or "").strip()
    pending = stream.get("pending_insights") or []
    top_insight = pending[0] if pending else ""

    return {
        "mood": mind.get("last_mood", "neutral") if not mind.get("error") else "—",
        "mood_score": mind.get("mood_score", 0) if not mind.get("error") else None,
        "curiosity_level": mind.get("curiosity_level", 1.0) if not mind.get("error") else None,
        "dominant_emotion": emotion.get("dominant", "curiosity") if not emotion.get("error") else "—",
        "current_mode": schedule.get("current_mode", "sleep"),
        "timezone": schedule.get("timezone", "UTC"),
        "now_iso": schedule.get("now_iso"),
        "growth_edge": growth_edge or top_insight or "—",
        "coherent": manifest.get("coherent"),
        "manifest_issues": manifest.get("issues", []),
        "errors": {
            "schedule": schedule.get("error"),
            "emotion": emotion.get("error"),
            "mind": mind.get("error"),
            "stream": stream.get("error"),
            "self_model": self_model.get("error"),
            "manifest": manifest.get("error"),
        },
    }
