# Import cycle detection (Phase 4)

Run: `PYTHONPATH=. .venv/bin/python scripts/check_import_cycles.py` from project root.

Module names are normalized to 3 segments (e.g. `app.core.foo`) for cycle reporting.

## Results (Phase 4 run)

**Cycle 1 (large):**  
`app.core.epistemics` → `app.core.personality` → `app.core.growth` → `app.core.self_awareness` → `app.core.ethics` → `app.core.dinner` → `app.core.emotions` → `app.core.awareness_bus` → `app.core.mood` → `app.core.inner_life` → `app.core.mama_gpt` → `app.core.astra_helpers` → `app.core.struggle_log` → `app.core.questions` → `app.interfaces.influence` → `app.interfaces.smart_mind_session` → `app.interfaces.mind_session` → `app.core.epistemics`

**Cycle 2:**  
`app.core.proactive` → `app.core.goals` → `app.core.proactive`

**Cycle 3:**  
`app.core.processing` → `app.core.astra_schedule` → `app.core.processing`

No fix was applied in Phase 4; this is discovery only. See `docs/tech-debt.md` for the "No automated cycle detection" entry and potential follow-up.
