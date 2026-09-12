"""
Astra Evolution: Corpus Export

Exports mind_file, dinner journal, Spark/ethics (via dinner), self_model, and
learning queue into a single JSONL corpus for training or context.
Schema: { "role", "content", "source", "timestamp" } per line.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root: parent of app/ (file is app/core/evolution/corpus_export.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CORPUS_PATH = _PROJECT_ROOT / "data" / "astra_corpus.jsonl"


def _normalize_entry(role: str, content: str, source: str, timestamp: Any = None) -> Dict[str, Any]:
    """Build a single corpus line."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    elif isinstance(timestamp, (int, float)):
        try:
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, OSError):
            timestamp = str(timestamp)
    elif not isinstance(timestamp, str):
        timestamp = str(timestamp)
    content = (content or "").strip()
    if not content:
        return None
    return {"role": role, "content": content, "source": source, "timestamp": timestamp}


def _load_mind() -> Optional[Dict[str, Any]]:
    """Load mind file from S3. Returns None on failure."""
    try:
        from app.interfaces.influence import load_mind
        return load_mind()
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug("Skipping mind_file: %s", e)
        return None


def _mind_to_entries(mind_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert mind_data to corpus entries."""
    entries = []
    if not mind_data:
        return entries

    for r in mind_data.get("self_reflections") or []:
        text = r if isinstance(r, str) else (r.get("content") or r.get("insight") or str(r))
        ent = _normalize_entry("reflection", text, "mind_file")
        if ent:
            entries.append(ent)

    for q in mind_data.get("self_questions") or []:
        text = q if isinstance(q, str) else (q.get("question") or str(q))
        ent = _normalize_entry("question", text, "mind_file")
        if ent:
            entries.append(ent)

    for k in mind_data.get("stored_knowledge") or []:
        text = k if isinstance(k, str) else (k.get("insight") or str(k))
        ent = _normalize_entry("knowledge", text, "mind_file")
        if ent:
            entries.append(ent)

    return entries


def _load_dinner_journal() -> List[Dict[str, Any]]:
    """Load dinner journal from S3. Returns [] on failure."""
    try:
        from app.core.dinner.dinner_journal import load_dinner_journal
        return load_dinner_journal()
    except Exception as e:
        print(f"[corpus_export] Skipping dinner journal: {e}")
        return []


def _dinner_to_entries(journal: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert dinner journal to corpus entries (topic + user/gpt responses = debate/resolution)."""
    entries = []
    for entry in journal:
        ts = entry.get("timestamp", "")
        content = entry.get("content", "").strip()
        if content:
            ent = _normalize_entry("dinner_topic", content, "dinner_journal", ts)
            if ent:
                entries.append(ent)
        user_r = entry.get("user_response", "").strip()
        if user_r:
            ent = _normalize_entry("dinner_user", user_r, "dinner_journal", ts)
            if ent:
                entries.append(ent)
        gpt_r = entry.get("gpt_response", "").strip()
        if gpt_r:
            ent = _normalize_entry("dinner_gpt", gpt_r, "dinner_journal", ts)
            if ent:
                entries.append(ent)
        spark = entry.get("spark_commentary", "").strip()
        if spark:
            ent = _normalize_entry("dinner_spark", spark, "dinner_journal", ts)
            if ent:
                entries.append(ent)
    return entries


def _load_self_model() -> List[Dict[str, Any]]:
    """Export self_model (snapshots, changes, surprise_log) to corpus entries."""
    entries = []
    try:
        from app.core.self_awareness.self_model import self_model
    except Exception as e:
        print(f"[corpus_export] Skipping self_model: {e}")
        return entries

    if self_model.current_model:
        m = self_model.current_model
        text = m.self_assessment or ""
        if text:
            entries.append(_normalize_entry("self_assessment", text, "self_model", m.timestamp))
        if m.growth_edge:
            entries.append(_normalize_entry("growth_edge", m.growth_edge, "self_model", m.timestamp))

    for c in getattr(self_model, "changes", [])[-100:]:
        ref = (c.reflection or "").strip()
        if ref:
            entries.append(_normalize_entry("self_change", ref, "self_model", c.timestamp))
        desc = f"{c.aspect}: {c.previous} → {c.current}"
        if c.trigger:
            desc += f" (trigger: {c.trigger})"
        entries.append(_normalize_entry("self_change_desc", desc, "self_model", c.timestamp))

    for s in getattr(self_model, "surprise_log", [])[-50:]:
        if isinstance(s, dict):
            content = s.get("description") or s.get("content") or json.dumps(s)
            ts = s.get("timestamp")
        else:
            content = str(s)
            ts = None
        ent = _normalize_entry("surprise", content, "self_model", ts)
        if ent:
            entries.append(ent)

    return entries


def _load_learning_queue() -> List[Dict[str, Any]]:
    """Export learning queue and open questions to corpus entries."""
    entries = []
    try:
        from app.core.proactive.learning_desire import LearningDesire
        ld = LearningDesire()
    except Exception as e:
        print(f"[corpus_export] Skipping learning queue: {e}")
        return entries

    for t in ld.queue or []:
        topic = getattr(t, "topic", None) or (t.get("topic") if isinstance(t, dict) else None)
        ctx = getattr(t, "context", None) or (t.get("context") if isinstance(t, dict) else None)
        content = topic or ""
        if ctx:
            content = f"{content}\n{ctx}" if content else ctx
        if content:
            ts = getattr(t, "added_at", None) or (t.get("added_at") if isinstance(t, dict) else None)
            ent = _normalize_entry("learning_topic", content.strip(), "learning_queue", ts)
            if ent:
                entries.append(ent)

    for q in ld.open_questions or []:
        question = getattr(q, "question", None) or (q.get("question") if isinstance(q, dict) else None)
        if question:
            ts = getattr(q, "generated_at", None) or (q.get("generated_at") if isinstance(q, dict) else None)
            ent = _normalize_entry("open_question", question.strip(), "learning_queue", ts)
            if ent:
                entries.append(ent)
        ans = getattr(q, "answer", None) or (q.get("answer") if isinstance(q, dict) else None)
        if ans:
            ts = getattr(q, "answered_at", None) or (q.get("answered_at") if isinstance(q, dict) else None)
            ent = _normalize_entry("open_question_answer", str(ans).strip(), "learning_queue", ts)
            if ent:
                entries.append(ent)

    return entries


def export_corpus(output_path: Optional[Union[str, Path]] = None) -> str:
    """
    Export all corpus sources to a single JSONL file.
    Returns the path written to.
    """
    output_path = Path(output_path) if output_path else DEFAULT_CORPUS_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_entries: List[Dict[str, Any]] = []

    mind_data = _load_mind()
    all_entries.extend(_mind_to_entries(mind_data or {}))

    journal = _load_dinner_journal()
    all_entries.extend(_dinner_to_entries(journal))

    all_entries.extend(_load_self_model())
    all_entries.extend(_load_learning_queue())

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_entries:
            if rec:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[corpus_export] Wrote {len(all_entries)} lines to {output_path}")
    return str(output_path)


def load_corpus_slice(path: Optional[Union[str, Path]] = None, max_lines: int = 500) -> List[Dict[str, Any]]:
    """
    Load a recent slice of the corpus (last max_lines lines).
    Used by local inference to inject context.
    """
    path = Path(path) if path else DEFAULT_CORPUS_PATH
    if not path.exists():
        return []
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    # Take last max_lines
    chosen = lines[-max_lines:] if len(lines) > max_lines else lines
    return [json.loads(l) for l in chosen]


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else None
    export_corpus(out)
