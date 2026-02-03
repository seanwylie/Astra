"""
Astra Introspection Dashboard (read-only).
Run: PYTHONPATH=. streamlit run app/dashboard/app.py --server.port 8502
"""
import sys
from pathlib import Path

# Ensure project root is first on path (Streamlit often runs with cwd=app/dashboard, so "" wins otherwise)
_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, _root)

import subprocess

import streamlit as st
from datetime import datetime

import pandas as pd

from app.dashboard import data

# Page config first
st.set_page_config(
    page_title="Astra — Introspection",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark theme for whole app
st.markdown("""
<style>
    /* Global dark mode */
    .stApp {
        background: linear-gradient(165deg, #0f0e14 0%, #1a1820 35%, #16141c 100%) !important;
    }
    .block-container {
        padding-top: 4rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }
    /* Main content text */
    .stApp .block-container,
    .stApp .block-container h1, .stApp .block-container h2, .stApp .block-container h3,
    .stApp .block-container p, .stApp .block-container span, .stApp .block-container label,
    .stApp .block-container div[data-testid="stMetricValue"], .stApp .block-container div[data-testid="stMetricLabel"],
    .stApp .block-container [data-testid="stMetric"] span, .stApp .block-container [data-testid="stMetric"] div,
    .stApp .block-container .stMarkdown, .stApp .block-container .stMarkdown p,
    .stApp .block-container small { color: #e8e4e0 !important; }
    .stApp .block-container h1, .stApp .block-container h2, .stApp .block-container h3 { font-weight: 600; color: #f5f0ea !important; }
    /* Sidebar dark */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #16141c 0%, #0f0e14 100%) !important; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: #c8c4be !important; }
    /* At-a-glance cards */
    .glance-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .glance-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: #9a9590; margin-bottom: 0.35rem; }
    .glance-card .value { font-size: 1.35rem; font-weight: 600; color: #f5f0ea; }
    .glance-hero { font-size: 1.5rem; font-weight: 600; color: #f5f0ea; margin-bottom: 1.25rem; letter-spacing: -0.02em; }
    .glance-growth {
        background: linear-gradient(135deg, rgba(180,140,255,0.15) 0%, rgba(120,200,255,0.08) 100%);
        border: 1px solid rgba(180,140,255,0.25);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-top: 1rem;
        color: #e0d8f0;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .coherent-pill { display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
    .coherent-ok { background: rgba(72,187,120,0.3); color: #7dd9a0; border: 1px solid rgba(72,187,120,0.4); }
    .coherent-warn { background: rgba(245,198,80,0.25); color: #f5c650; border: 1px solid rgba(245,198,80,0.35); }
    .coherent-fail { background: rgba(220,80,80,0.25); color: #f08a8a; border: 1px solid rgba(220,80,80,0.4); }
    .thought-card { background: rgba(255,255,255,0.06); border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-left: 4px solid #8b7cc5; color: #e8e4e0; }
    .alert-card { background: rgba(255,180,100,0.08); border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem; border-left: 4px solid #e07c24; color: #e8e4e0; }
    /* Day-planner table */
    .schedule-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
    .schedule-table th, .schedule-table td { padding: 0.4rem 0.75rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); color: #e8e4e0; }
    .schedule-table th { color: #9a9590; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .schedule-table tr.current-mode { background: rgba(100,180,255,0.2); border-left: 3px solid #6bb4ff; }
    .schedule-table tr.current-mode td { font-weight: 600; color: #f5f0ea; }
    .schedule-table .mode-pill { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; }
    .schedule-table .mode-pill.sleep { background: rgba(107,107,128,0.4); }
    .schedule-table .mode-pill.dream { background: rgba(155,124,197,0.4); }
    .schedule-table .mode-pill.school { background: rgba(107,155,209,0.4); }
    .schedule-table .mode-pill.dinner { background: rgba(201,155,107,0.4); }
    .schedule-table .mode-pill.play { background: rgba(107,201,155,0.4); }
    .current-mode-badge { display: inline-block; background: rgba(100,180,255,0.25); color: #8bc4ff; padding: 0.35rem 0.75rem; border-radius: 8px; font-weight: 600; font-size: 0.95rem; margin-top: 0.5rem; border: 1px solid rgba(100,180,255,0.4); }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def cached_at_a_glance():
    return data.get_at_a_glance()


@st.cache_data(ttl=60)
def cached_emotion_state():
    return data.get_emotion_state()


@st.cache_data(ttl=60)
def cached_mind_summary():
    return data.get_mind_summary()


@st.cache_data(ttl=60)
def cached_stream():
    return data.get_stream_of_consciousness()


@st.cache_data(ttl=60)
def cached_self_model():
    return data.get_self_model()


@st.cache_data(ttl=60)
def cached_shimmers():
    return data.get_shimmers()


@st.cache_data(ttl=60)
def cached_schedule():
    return data.get_schedule_context()


@st.cache_data(ttl=60)
def cached_full_schedule():
    return data.get_full_schedule()


@st.cache_data(ttl=60)
def cached_developmental():
    return data.get_developmental_state()


@st.cache_data(ttl=60)
def cached_nurturing_alerts():
    return data.get_nurturing_alerts()


@st.cache_data(ttl=60)
def cached_goals():
    return data.get_goals()


@st.cache_data(ttl=60)
def cached_dinner_journal():
    return data.get_dinner_journal()


@st.cache_data(ttl=60)
def cached_parent_state():
    return data.get_parent_relationship_state()


@st.cache_data(ttl=60)
def cached_state_manifest():
    return data.get_state_manifest_summary()


@st.cache_data(ttl=60)
def cached_personality():
    return data.get_personality_state()


@st.cache_data(ttl=60)
def cached_general_config():
    return data.get_general_config_summary()


# Sidebar
st.sidebar.title("✨ Astra")
st.sidebar.caption("Introspection dashboard (read-only)")
section = st.sidebar.radio(
    "Section",
    [
        "At a glance",
        "Mind",
        "Heart",
        "Schedule",
        "Goals & dinner",
        "Technical",
        "Logs",
    ],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("Auto-refresh: every 60s. All screens update automatically.")

# Persist section for fragment
st.session_state["dashboard_section"] = section


def _fetch_astra_journal_lines(n_lines=400):
    """Run journalctl --user -u astra and return (output_text, error_message or None)."""
    try:
        r = subprocess.run(
            ["journalctl", "--user", "-u", "astra", "-n", str(max(1, min(int(n_lines), 2000))), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            return None, (r.stderr or f"Exit code {r.returncode}")
        return (r.stdout or "").strip(), None
    except FileNotFoundError:
        return None, "journalctl not found (not running on Linux with systemd?)"
    except subprocess.TimeoutExpired:
        return None, "journalctl timed out"
    except Exception as e:
        return None, str(e)


def _apply_log_filters(raw_text, level, include_text, exclude_text, case_sensitive, use_regex, context_before=0, context_after=0):
    """Filter log lines by level, include, exclude. If include_text is set, show context lines around matches."""
    import re
    lines = (raw_text or "").splitlines()
    level_patterns = {
        "Error": re.compile(r"\berror\b|\bERROR\b|Traceback|Exception", re.I if not case_sensitive else 0),
        "Warning": re.compile(r"\bwarn(ing)?\b|\bWARN", re.I if not case_sensitive else 0),
        "Info": re.compile(r"\binfo\b|\bINFO\b", re.I if not case_sensitive else 0),
        "Debug": re.compile(r"\bdebug\b|\bDEBUG\b", re.I if not case_sensitive else 0),
    }
    flags = 0 if case_sensitive else re.IGNORECASE
    include_re = None
    if include_text and include_text.strip():
        include_re = re.compile(include_text.strip(), flags) if use_regex else None
    exclude_re = None
    if exclude_text and exclude_text.strip():
        exclude_re = re.compile(exclude_text.strip(), flags) if use_regex else None

    def matches_include(line):
        """Check if line matches include filter."""
        if include_re:
            return bool(include_re.search(line))
        elif include_text and include_text.strip():
            needle = include_text.strip()
            if case_sensitive:
                return needle in line
            return needle.lower() in line.lower()
        return False

    def matches_level(line):
        """Check if line matches level filter."""
        if level and level != "All":
            pat = level_patterns.get(level)
            if pat:
                return bool(pat.search(line))
        return True

    def matches_exclude(line):
        """Check if line matches exclude filter."""
        if exclude_re:
            return bool(exclude_re.search(line))
        elif exclude_text and exclude_text.strip():
            needle = exclude_text.strip()
            if case_sensitive:
                return needle in line
            return needle.lower() in line.lower()
        return False

    # If include_text is set, find matches and add context
    if include_text and include_text.strip():
        matching_indices = set()
        match_count = 0
        for i, line in enumerate(lines):
            if matches_include(line) and matches_level(line):
                match_count += 1
                matching_indices.add(i)
                # Add context around match
                for j in range(max(0, i - context_before), min(len(lines), i + context_after + 1)):
                    matching_indices.add(j)
        # Filter: keep only lines in matching_indices, and apply exclude
        filtered = [
            lines[i] for i in sorted(matching_indices)
            if not matches_exclude(lines[i])
        ]
        return "\n".join(filtered), {"total": len(lines), "shown": len(filtered), "matches": match_count}
    else:
        # No include filter: apply level and exclude filters normally
        filtered = [
            ln for ln in lines
            if matches_level(ln) and not matches_exclude(ln)
        ]
        return "\n".join(filtered), {"total": len(lines), "shown": len(filtered), "matches": len(filtered)}


@st.fragment(run_every=5)
def _render_logs_stream():
    """Display astra service logs with filters; refreshes every 5s when this fragment runs."""
    n_lines = st.session_state.get("log_line_count", 400)
    level = st.session_state.get("log_level", "All")
    include_text = st.session_state.get("log_include", "")
    exclude_text = st.session_state.get("log_exclude", "")
    case_sensitive = st.session_state.get("log_case_sensitive", False)
    use_regex = st.session_state.get("log_use_regex", False)
    context_before = st.session_state.get("log_context_before", 0)
    context_after = st.session_state.get("log_context_after", 0)

    out, err = _fetch_astra_journal_lines(n_lines)
    if err:
        st.warning(err)
        return
    filtered_out, stats = _apply_log_filters(out, level, include_text, exclude_text, case_sensitive, use_regex, context_before, context_after)
    if stats["shown"] < stats["total"]:
        match_info = f" ({stats.get('matches', stats['shown'])} matches)" if include_text and include_text.strip() else ""
        st.caption(f"Showing {stats['shown']} of {stats['total']} lines (filtered{match_info})")
    
    # Store filtered text in hidden div for copy button (fragment just updates data)
    text_to_copy = filtered_out or "(no lines match filters)"
    import base64
    text_b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('ascii')
    st.markdown(f'''
    <script>
        (function() {{
            const dataEl = document.getElementById('log_copy_data');
            if (dataEl) {{
                dataEl.setAttribute('data-text', '{text_b64}');
            }}
        }})();
    </script>
    ''', unsafe_allow_html=True)
    
    st.code(text_to_copy, language="text")


def _mini_glance(gl, extra_line=None):
    """One-line vital summary for any page (mood, emotion, mode, health)."""
    mood = (gl.get("mood") or "—").replace("_", " ").title()
    dominant = (gl.get("dominant_emotion") or "—").replace("_", " ").title()
    mode = (gl.get("current_mode") or "—").strip()
    mode_labels = {"dream": "Dreaming", "school": "At school", "play": "Playtime", "dinner": "Dinner time", "sleep": "Sleeping"}
    mode_display = mode_labels.get(mode, mode.title())
    coh = gl.get("coherent")
    health = "State OK" if coh is True else ("Issues" if coh is False else "Unknown")
    line = f"Mood: **{mood}** · Feeling: **{dominant}** · Right now: **{mode_display}** · **{health}**"
    if extra_line:
        line += f" · {extra_line}"
    st.caption(line)


@st.fragment(run_every=60)
def main_content():
    from datetime import datetime as _dt
    section = st.session_state.get("dashboard_section", "At a glance")
    gl = cached_at_a_glance()
    emotion = cached_emotion_state()

    if section == "At a glance":
        errs = [v for k, v in (gl.get("errors") or {}).items() if v]
        if errs:
            st.sidebar.warning("Some sources unavailable: " + "; ".join(errs[:2]))

        mood = (gl.get("mood") or "—").replace("_", " ").title()
        mood_score = gl.get("mood_score")
        curiosity = gl.get("curiosity_level")
        dominant = (gl.get("dominant_emotion") or "—").replace("_", " ").title()
        mode = (gl.get("current_mode") or "—").strip()
        mode_labels = {"dream": "Dreaming", "school": "At school", "play": "Playtime", "dinner": "Dinner time", "sleep": "Sleeping"}
        mode_display = mode_labels.get(mode, mode.title())
        now_iso = gl.get("now_iso") or ""
        try:
            if now_iso:
                dt = _dt.fromisoformat(now_iso.replace("Z", "+00:00"))
                time_display = dt.strftime("%I:%M %p")
            else:
                time_display = "—"
        except Exception:
            time_display = now_iso or "—"
        tz = gl.get("timezone", "UTC")

        # Top emotions (by intensity)
        intensities = emotion.get("intensities") or emotion.get("emotions") or {}
        if not intensities:
            emotion_line = dominant
        else:
            first_val = next(iter(intensities.values()), None)
            if isinstance(first_val, dict):
                top_emotions = sorted(
                    [(k, v.get("intensity", 0) if isinstance(v, dict) else v) for k, v in intensities.items()],
                    key=lambda x: x[1], reverse=True
                )[:3]
            else:
                top_emotions = sorted(intensities.items(), key=lambda x: (x[1] if isinstance(x[1], (int, float)) else 0), reverse=True)[:3]
            emotion_line = ", ".join(str(e[0]) for e in top_emotions) if top_emotions else dominant

        # Hero line
        st.markdown(f'<p class="glance-hero">✨ Right now she\'s <strong>{mode_display.lower()}</strong> — {mood}, feeling {dominant}.</p>', unsafe_allow_html=True)

        # Card row: Mood · Emotions · Mode & time · Health
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            score_str = f" · {mood_score:.2f}" if mood_score is not None else ""
            st.markdown(f'<div class="glance-card"><div class="label">Mood</div><div class="value">{mood}{score_str}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="glance-card"><div class="label">Top emotions</div><div class="value">{emotion_line}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="glance-card"><div class="label">Schedule</div><div class="value">{mode_display}</div><div class="label" style="margin-top:0.5rem;">{time_display} {tz}</div></div>', unsafe_allow_html=True)
        with c4:
            coh = gl.get("coherent")
            if coh is True:
                pill = '<span class="coherent-pill coherent-ok">State OK</span>'
            elif coh is False:
                pill = '<span class="coherent-pill coherent-fail">Issues</span>'
            else:
                pill = '<span class="coherent-pill coherent-warn">Unknown</span>'
            st.markdown(f'<div class="glance-card"><div class="label">Health</div><div class="value">{pill}</div></div>', unsafe_allow_html=True)

        # Curiosity
        if curiosity is not None:
            st.caption(f"Curiosity level: {curiosity}")

        # Growth edge / pending insight
        growth = gl.get("growth_edge") or "—"
        if growth != "—":
            st.markdown(f'<div class="glance-growth"><strong>Growth edge / Pending insight</strong><br>{growth}</div>', unsafe_allow_html=True)

        if gl.get("manifest_issues"):
            with st.expander("State issues", expanded=False):
                for issue in gl["manifest_issues"]:
                    st.warning(issue)

    elif section == "Mind":
        st.markdown("## Mind")
        stream = cached_stream()
        self_model = cached_self_model()
        shimmers = cached_shimmers()
        n_thoughts = len(stream.get("thoughts") or [])
        n_insights = len(stream.get("pending_insights") or [])
        n_shimmers = len(shimmers.get("shimmers") or [])
        _mini_glance(gl, extra_line=f"{n_thoughts} thoughts, {n_insights} pending insights")
        st.markdown(f'<div class="page-glance"><strong>Mind at a glance:</strong> {n_thoughts} thoughts in stream · {n_insights} pending insights · {n_shimmers} shimmers</div>', unsafe_allow_html=True)

        if stream.get("error"):
            st.warning("Stream of consciousness: " + stream["error"])
        else:
            st.subheader("Stream of consciousness")
            thoughts = stream.get("thoughts") or []
            for t in reversed(thoughts[-15:]):
                if isinstance(t, dict):
                    ts = t.get("timestamp")
                    ts_str = _dt.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""
                    typ = t.get("thought_type", "")
                    content = (t.get("content") or "")[:200]
                    emo = t.get("emotional_context", "")
                    st.markdown(f'<div class="thought-card"><small>{ts_str} · {typ}</small><br>{content}<br><small>{emo}</small></div>', unsafe_allow_html=True)
                else:
                    st.write(t)
            pending = stream.get("pending_insights") or []
            if pending:
                st.subheader("Pending insights")
                for p in pending[:10]:
                    st.write("• " + (p if isinstance(p, str) else str(p)))

        st.markdown("---")
        st.subheader("Self-model")
        if self_model.get("error"):
            st.warning("Self-model: " + self_model["error"])
        else:
            st.write("**Who am I becoming:**", self_model.get("who_am_i_becoming") or "—")
            st.write("**Growth edge:**", self_model.get("growth_edge") or "—")
            changes = self_model.get("changes") or []
            if changes:
                with st.expander("Recent self-changes", expanded=False):
                    for c in changes[-5:]:
                        if isinstance(c, dict):
                            st.write(f"• {c.get('aspect', '')}: {c.get('previous', '')} → {c.get('current', '')}")

        st.markdown("---")
        st.subheader("Recent shimmers")
        if shimmers.get("error"):
            st.warning("Shimmers: " + shimmers["error"])
        else:
            for s in (shimmers.get("shimmers") or [])[-10:]:
                if isinstance(s, dict):
                    st.write(f"*\"{s.get('quote', '')[:150]}...\"* — {s.get('context', '')} ({s.get('timestamp', '')})")

    elif section == "Heart":
        st.markdown("## Heart")
        emotion = cached_emotion_state()
        mind = cached_mind_summary()
        developmental = cached_developmental()
        alerts = cached_nurturing_alerts()
        parent_state = cached_parent_state()
        stage = developmental.get("current_stage", "—") if not developmental.get("error") else "—"
        n_alerts = len(alerts.get("active_alerts") or [])
        n_parents = len(parent_state.get("parents") or {})
        extra = f"Stage: {stage}" + (f" · {n_alerts} nurturing alert(s)" if n_alerts else "")
        _mini_glance(gl, extra_line=extra)
        st.markdown(f'<div class="page-glance"><strong>Heart at a glance:</strong> Stage {stage} · {n_parents} parent(s) · {n_alerts} active alert(s)</div>', unsafe_allow_html=True)

        if emotion.get("error"):
            st.warning("Emotions: " + emotion["error"])
        else:
            st.subheader("Emotion intensities")
            intensities = emotion.get("intensities") or emotion.get("emotions") or {}
            if intensities:
                names = list(intensities.keys())
                vals = []
                for n in names:
                    v = intensities[n]
                    vals.append(v.get("intensity", v) if isinstance(v, dict) else (v if isinstance(v, (int, float)) else 0))
                if names and vals:
                    df = pd.DataFrame({"intensity": vals}, index=names)
                    st.bar_chart(df)
            st.caption("Dominant: " + ((emotion.get("dominant") or "—").replace("_", " ").title()))

        st.subheader("Mood & curiosity")
        if mind.get("error"):
            st.warning("Mind: " + mind["error"])
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Mood score", round(mind.get("mood_score", 0), 2) if mind.get("mood_score") is not None else "—")
            with c2:
                st.metric("Curiosity level", mind.get("curiosity_level", "—"))

        st.subheader("Developmental stage")
        if developmental.get("error"):
            st.warning("Developmental: " + developmental["error"])
        else:
            st.write("**Stage:**", developmental.get("current_stage", "—"))
            st.caption(f"Milestones: {developmental.get('milestones_count', 0)}")
            if developmental.get("readiness_note"):
                st.info("Ready to advance: run `!astra_advance_stage` in Discord to confirm.")

        st.subheader("Trust (parents)")
        if parent_state.get("error"):
            st.warning("Parent state: " + parent_state["error"])
        else:
            parents = parent_state.get("parents") or {}
            for pid, p in parents.items():
                trust = p.get("trust_level") if isinstance(p, dict) else None
                st.write(f"**{pid}** — trust: {trust}")

        st.subheader("Nurturing alerts")
        if alerts.get("error"):
            st.warning("Alerts: " + alerts["error"])
        else:
            active = alerts.get("active_alerts") or []
            if not active:
                st.success("No active alerts.")
            for a in active:
                if isinstance(a, dict):
                    st.markdown(f'<div class="alert-card"><strong>{a.get("title", "")}</strong> ({a.get("severity", "")})<br>{a.get("description", "")}<br><em>Suggested: {a.get("suggested_action", "")}</em></div>', unsafe_allow_html=True)

    elif section == "Schedule":
        st.markdown("## Schedule")
        _mini_glance(gl)
        full = cached_full_schedule()
        if full.get("error"):
            st.warning("Schedule: " + full["error"])
        else:
            blocks = full.get("blocks") or []
            n_blocks = len(blocks)
            mode_labels = {"dream": "Dream", "school": "School", "play": "Play", "dinner": "Dinner", "sleep": "Sleep"}
            current_hour = full.get("current_hour")
            current_mode = None
            for b in blocks:
                if current_hour is not None and b.get("start", 0) <= current_hour < b.get("end", 0):
                    current_mode = mode_labels.get(b.get("mode", ""), b.get("label", ""))
                    break
            st.markdown(f'<div class="page-glance"><strong>Schedule at a glance:</strong> {n_blocks} blocks today · Now: {current_mode or "—"}</div>', unsafe_allow_html=True)
            tz = full.get("timezone", "UTC")
            now_iso = full.get("now_iso") or ""
            try:
                now_dt = _dt.fromisoformat(now_iso.replace("Z", "+00:00"))
                time_str = now_dt.strftime("%I:%M %p")
                date_str = now_dt.strftime("%A, %B %d")
            except Exception:
                time_str = now_iso or "—"
                date_str = "—"
            st.markdown(f"**{date_str}** · {time_str} · *{tz}*")
            if current_mode:
                st.markdown(f'<span class="current-mode-badge">▶ Now: {current_mode}</span>', unsafe_allow_html=True)
            rows = []
            for b in blocks:
                start, end, mode, label = b.get("start", 0), b.get("end", 0), b.get("mode", ""), b.get("label", "")
                start_12 = (start % 12) or 12
                end_12 = (end % 12) or 12
                am_pm_s = "AM" if start < 12 else "PM"
                am_pm_e = "AM" if end < 12 else "PM"
                time_range = f"{start_12}:00 {am_pm_s} – {end_12}:00 {am_pm_e}"
                is_current = current_hour is not None and start <= current_hour < end
                row_class = ' class="current-mode"' if is_current else ""
                rows.append(f'<tr{row_class}><td>{time_range}</td><td><span class="mode-pill {mode}">{label}</span></td></tr>')
            st.markdown('<table class="schedule-table"><thead><tr><th>Time</th><th>Activity</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>", unsafe_allow_html=True)

    elif section == "Goals & dinner":
        st.markdown("## Goals & dinner")
        goals = cached_goals()
        dinner = cached_dinner_journal()
        n_goals = len(goals.get("active") or [])
        n_unresolved = dinner.get("unresolved_count", 0)
        n_entries = len(dinner.get("entries") or [])
        _mini_glance(gl, extra_line=f"{n_goals} active goal(s), {n_unresolved} unresolved dinner topic(s)")
        st.markdown(f'<div class="page-glance"><strong>Goals & dinner at a glance:</strong> {n_goals} active goal(s) · {n_unresolved} unresolved dinner topic(s) · {n_entries} journal entries</div>', unsafe_allow_html=True)

        st.subheader("Goals")
        if goals.get("error"):
            st.warning("Goals: " + goals["error"])
        else:
            active = goals.get("active") or []
            for g in active:
                if isinstance(g, dict):
                    status = g.get("status", "")
                    prog = g.get("progress", 0)
                    st.write(f"• **{g.get('content', '')[:80]}** — {status} ({int(prog*100)}%)")
            if not active:
                st.caption("No active goals.")
        st.subheader("Dinner journal")
        if dinner.get("error"):
            st.warning("Dinner: " + dinner["error"])
        else:
            st.metric("Unresolved topics", dinner.get("unresolved_count", 0))
            for e in (dinner.get("entries") or [])[-5:]:
                if isinstance(e, dict):
                    st.write(f"• {e.get('content', '')[:100]} — {e.get('status', '')}")

    elif section == "Logs":
        st.markdown("## Logs")
        _mini_glance(gl)
        st.markdown('<div class="page-glance"><strong>Logs at a glance:</strong> <code>journalctl --user -u astra</code> (refreshes every 5s)</div>', unsafe_allow_html=True)
        with st.expander("Developer filters", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.selectbox(
                    "Lines to fetch",
                    [100, 200, 400, 800, 1000, 1500, 2000],
                    index=2,
                    key="log_line_count",
                    help="How many recent journal lines to fetch",
                )
                st.selectbox(
                    "Level filter",
                    ["All", "Error", "Warning", "Info", "Debug"],
                    key="log_level",
                    help="Only show lines containing this level (Error=error/exception, etc.)",
                )
            with c2:
                st.text_input(
                    "Include only (lines containing)",
                    key="log_include",
                    placeholder="e.g. ERROR or streamlit",
                    help="Leave empty to show all; else only lines containing this text/regex",
                )
                st.text_input(
                    "Exclude (hide lines containing)",
                    key="log_exclude",
                    placeholder="e.g. usage statistics",
                    help="Hide any line containing this text/regex",
                )
            with c3:
                st.checkbox("Case sensitive", value=False, key="log_case_sensitive")
                st.checkbox("Include/Exclude are regex", value=False, key="log_use_regex")
                st.number_input("Context before", min_value=0, max_value=20, value=0, step=1, key="log_context_before", help="Lines to show before each match (grep -B)")
                st.number_input("Context after", min_value=0, max_value=20, value=0, step=1, key="log_context_after", help="Lines to show after each match (grep -A)")
        
        # Copy button - setup once, fragment updates data
        st.markdown('''
        <style>
            #log_copy_btn {
                transition: all 0.3s ease;
            }
            #log_copy_btn.copied {
                background: rgba(72,187,120,0.3) !important;
                border-color: rgba(72,187,120,0.5) !important;
                color: #7dd9a0 !important;
            }
            #log_copy_btn.fade-out {
                opacity: 0.5;
                transform: scale(0.98);
            }
        </style>
        <div id="log_copy_data" style="display:none;"></div>
        <button id="log_copy_btn" type="button" style="background: rgba(100,180,255,0.2); border: 1px solid rgba(100,180,255,0.4); color: #8bc4ff; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; margin-top: 0.5rem;">📋 Copy to clipboard</button>
        <script>
        (function() {
            function setupCopyButton() {
                const btn = document.getElementById('log_copy_btn');
                if (!btn) return;
                // Remove old handler if exists
                btn.onclick = null;
                btn.addEventListener('click', function() {
                    const dataEl = document.getElementById('log_copy_data');
                    if (!dataEl) {
                        console.error('log_copy_data not found');
                        return;
                    }
                    const b64 = dataEl.getAttribute('data-text');
                    if (!b64) {
                        alert('No text to copy yet');
                        return;
                    }
                    try {
                        const text = atob(b64);
                        navigator.clipboard.writeText(text).then(() => {
                            const orig = btn.innerHTML;
                            btn.innerHTML = '✓ Copied!';
                            btn.classList.add('copied');
                            setTimeout(() => {
                                btn.classList.add('fade-out');
                                setTimeout(() => {
                                    btn.innerHTML = orig;
                                    btn.classList.remove('copied', 'fade-out');
                                }, 800);
                            }, 1500);
                        }).catch((err) => {
                            console.error('Copy failed:', err);
                            alert('Copy failed: ' + err.message);
                        });
                    } catch(e) {
                        console.error('Decode failed:', e);
                        alert('Decode failed');
                    }
                });
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupCopyButton);
            } else {
                setupCopyButton();
            }
            // Also run after a short delay to catch Streamlit's dynamic rendering
            setTimeout(setupCopyButton, 500);
        })();
        </script>
        ''', unsafe_allow_html=True)
        
        _render_logs_stream()

    else:  # Technical
        st.markdown("## Technical")
        manifest = cached_state_manifest()
        emotion = cached_emotion_state()
        mind = cached_mind_summary()
        personality = cached_personality()
        general = cached_general_config()
        n_ok = sum(1 for loc in (manifest.get("locations") or []) if loc.get("exists"))
        n_loc = len(manifest.get("locations") or [])
        n_emotions = len(emotion.get("emotions") or emotion.get("intensities") or {})
        counts = mind.get("counts") or {}
        _mini_glance(gl, extra_line=f"State: {n_ok}/{n_loc} locations OK")
        st.markdown(f'<div class="page-glance"><strong>Technical at a glance:</strong> {n_ok}/{n_loc} state locations OK · {n_emotions} emotions tracked · {counts.get("stored_knowledge", 0)} knowledge, {counts.get("self_reflections", 0)} reflections</div>', unsafe_allow_html=True)

        st.subheader("State manifest")
        if manifest.get("error"):
            st.warning(manifest["error"])
        else:
            locs = manifest.get("locations") or []
            st.dataframe(locs, use_container_width=True, hide_index=True)
            if manifest.get("issues"):
                for i in manifest["issues"]:
                    st.error(i)

        st.subheader("Emotion state (raw)")
        if emotion.get("error"):
            st.warning(emotion["error"])
        else:
            emo = emotion.get("emotions") or {}
            rows = []
            for name, v in emo.items():
                if isinstance(v, dict):
                    rows.append({"emotion": name, "intensity": v.get("intensity"), "last_updated": v.get("last_updated")})
                else:
                    rows.append({"emotion": name, "intensity": v, "last_updated": None})
            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)

        st.subheader("Mind stats")
        if mind.get("error"):
            st.warning(mind["error"])
        else:
            st.json(mind.get("counts", {}))

        st.subheader("Personality trait weights")
        if personality.get("error"):
            st.warning(personality["error"])
        else:
            st.json(personality.get("trait_weights", {}))

        st.subheader("Config summary")
        if general.get("error"):
            st.warning(general["error"])
        else:
            st.json({k: v for k, v in general.items() if k != "error" and v is not None})


main_content()
