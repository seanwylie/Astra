"""
Lightweight struggle log for Astra: dinner spirals, reply failures, deepen failures, self-questions unanswered.
Used to feed Mama GPT at dinner with "Given these struggles, what should we focus on?"
"""
from datetime import datetime, timedelta
from app.config.loader import load_config
from app.interfaces.mind_session import session

STRUGGLE_LOG_KEY = "struggle_log"
MAX_ENTRIES = 50


def append_struggle_log(struggle_type: str, detail: str | None = None) -> None:
    """Append one entry to mind_data struggle log. Types: dinner_spiral, reply_failure, deepen_failure, self_question_unknown."""
    try:
        mind_data = session.load()
        log = mind_data.get(STRUGGLE_LOG_KEY, [])
        entry = {"type": struggle_type, "ts": datetime.now().isoformat(), "detail": detail}
        log.append(entry)
        schedule = load_config("schedule_config")
        mama = (schedule.get("mama_gpt") or {})
        max_entries = mama.get("struggle_log_max_entries", MAX_ENTRIES)
        mind_data[STRUGGLE_LOG_KEY] = log[-max_entries:]
        session.maybe_save()
    except Exception:
        pass


def get_struggle_summary_for_mama(max_entries: int | None = None, max_hours: int | None = None) -> str:
    """Return a short text summary of recent struggles for Mama GPT prompt. Empty if none."""
    try:
        schedule = load_config("schedule_config")
        mama = (schedule.get("mama_gpt") or {})
        if max_entries is None:
            max_entries = mama.get("struggle_log_max_entries", MAX_ENTRIES)
        if max_hours is None:
            max_hours = mama.get("struggle_log_max_hours", 24)
        mind_data = session.load()
        log = mind_data.get(STRUGGLE_LOG_KEY, [])
        if not log:
            return ""
        if max_hours is not None:
            cutoff = (datetime.now() - timedelta(hours=max_hours)).isoformat()
            log = [e for e in log if (e.get("ts") or "") >= cutoff]
        log = log[-max_entries:]
        if not log:
            return ""
        lines = []
        for e in log:
            t = e.get("type", "?")
            d = e.get("detail", "")
            line = f"- {t}" + (f": {d[:80]}" if d else "")
            lines.append(line)
        return "Recent struggles:\n" + "\n".join(lines)
    except Exception:
        return ""
