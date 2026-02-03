# Astra Codebase Audit (Post–Phase 2) and Phase 3 Plan

This document re-audits the codebase against the 16 categories after Phase 1 and Phase 2, then proposes a concrete **Phase 3** plan.

**Done in Phase 1:** Single config loader, dead code removed (discord_astra, utils/config_loader), hardcoded paths fixed, Makefile + pyproject.toml, pytest markers, stale rules removed.

**Done in Phase 2:** `app/exceptions.py` and use in config + influence; print→logger in message_event, message_bus, message_processing_service, message_generator; S3/OpenAI timeouts and retries; pre-commit; GitHub Actions CI; reliability note in README; conftest `minimal_mind_dict` fixture; ADRs 001 and 002.

---

## 1) Architecture & design sanity

| Area | Status | Notes |
|------|--------|------|
| **Modularization** | Weak | `message_event.py` (~1155 lines) and `message_bus.py` (~1661 lines) unchanged in size; still the main “god module” candidates. |
| **Layering** | Weak | Core still imports config, interfaces, logging. `utils/time_utils` imports from `app`. No enforced boundaries. |
| **API contracts** | Partial | No public REST API. Internal interfaces stable; `app.exceptions` gives clearer contracts. |
| **Cycles** | Unknown | No automated cycle detection. |
| **Error handling** | Improved | Typed exceptions in use; propagation and retries improved in Phase 2. More call sites could use `app.exceptions`. |
| **Config** | Good | Single loader, env validation, `ConfigurationError` on validation failure. |
| **Deprecation** | Missing | No formal deprecation plan. |

---

## 2) Reduce redundancy & complexity

| Area | Status | Notes |
|------|--------|------|
| **Dead code** | Good | Legacy and duplicate loader removed. maintenance/legacy holds old discord_astra. |
| **DRY** | Weak | Optional integration blocks still duplicated in message_event and message_bus. Repeated `load_config("general_config")` in many files. |
| **Control flow** | Weak | message_event and message_bus still have deep nesting and long functions. |
| **Primitive obsession** | Mixed | Many dict/str flows; some value types could help. |
| **Duplicate data models** | Partial | Mind shape implied; single load/save in influence. |
| **Patterns** | Ad hoc | No shared integration registry. |

---

## 3) Code health & readability

| Area | Status | Notes |
|------|--------|------|
| **Naming** | Good | Consistent; legacy “beta” comment fixed in message_event. |
| **Style** | Good | Makefile, pyproject, pre-commit, CI. |
| **Type safety** | Partial | Many type hints; mypy in CI with `\|\| true` (non-blocking). |
| **Docstrings** | Mixed | Present in many places; large modules need more. |
| **Cleverness** | Low | Mostly straightforward. |
| **print()** | Partial | **~276 print() calls remain in 52 files.** Hot paths fixed in Phase 2; rest are in core/, services/, etc. |

---

## 4) Testability & automated confidence

| Area | Status | Notes |
|------|--------|------|
| **Pyramid** | Partial | Markers and `minimal_mind_dict` fixture. Two tests marked integration. |
| **Coverage** | Low | No coverage in CI; 9 test files. |
| **Golden/snapshots** | None | No snapshot tests. |
| **Property-based** | None | No hypothesis. |
| **Flake** | Unknown | LOG_LEVEL in conftest; no explicit timeouts/isolation. |
| **Fixtures** | Partial | One shared fixture; no config or session factories. |

---

## 5) Security audit & hardening

| Area | Status | Notes |
|------|--------|------|
| **Threat model** | Missing | Not documented. |
| **SCA** | Missing | No dependency vulnerability scanning in CI. |
| **Secrets** | Good | Rules + .gitignore; env for tokens. |
| **AuthN/AuthZ** | Minimal | Discord bot token; no RBAC. |
| **Input validation** | Partial | Config validated; no formal mind or Discord input schema. |
| **Secure defaults** | N/A | No web server in main app; Streamlit is optional. |
| **Security logging** | Partial | get_logger; no dedicated auth/suspicious logging. |
| **Supply chain** | Partial | Pinned versions; **no lockfile**; no signed builds. |

---

## 6) Performance audit & tuning

| Area | Status | Notes |
|------|--------|------|
| **Profiling** | None | No baseline. |
| **Hot path** | Unknown | No algorithmic audit. |
| **DB** | N/A | S3/JSON. |
| **Caching** | Partial | Config cached; mind in memory. |
| **Concurrency** | Mixed | Async in places; no formal strategy. |
| **Batching/backpressure** | Unknown | No explicit strategy. |
| **Payload** | Unknown | No trimming audit. |

---

## 7) Reliability, resilience & operability

| Area | Status | Notes |
|------|--------|------|
| **SLOs/SLIs** | Missing | Not defined. |
| **Timeouts/retries** | Improved | S3 and OpenAI have timeouts/retries (Phase 2). |
| **Idempotency** | Documented | Mind save documented as overwrite in README. |
| **Graceful degradation** | Good | *_AVAILABLE flags. |
| **Chaos** | None | No fault injection. |
| **Runbooks** | Missing | No runbooks in repo. |
| **Postmortem** | Missing | No process doc. |

---

## 8) Observability & telemetry

| Area | Status | Notes |
|------|--------|------|
| **Structured logging** | Partial | get_logger; no correlation IDs. |
| **Metrics** | Partial | prometheus_integration exists; no dashboard/alert doc. |
| **Tracing** | None | No distributed tracing. |
| **Dashboards** | Partial | Streamlit dashboard; no ops dashboards doc. |
| **Alerts** | Missing | No alert rules in repo. |

---

## 9) Data quality & correctness

| Area | Status | Notes |
|------|--------|------|
| **Schema** | Implicit | Mind file shape not formalized. |
| **Validation at boundaries** | Partial | Config validated; mind load/save not schema-validated. |
| **Backfills/repair** | Partial | maintenance/ scripts. |
| **Consistency** | Undocumented | No explicit consistency doc. |
| **Retention/deletion** | Missing | No compliance doc. |

---

## 10) Dependencies & upgrades

| Area | Status | Notes |
|------|--------|------|
| **Version plan** | Good | requirements.txt + pyproject.toml; pinned. |
| **Deprecated APIs** | Unknown | No audit. |
| **Abandonware** | Unknown | No audit. |
| **Lockfile** | Missing | **No pip-compile or requirements lock.** |
| **Automated PRs** | Missing | No Dependabot/Renovate. |

---

## 11) DevEx

| Area | Status | Notes |
|------|--------|------|
| **Bootstrap** | Partial | README + setup_venv; no one-command bootstrap. |
| **Scripts** | Good | Makefile, pre-commit. |
| **Pre-commit** | Good | black, isort, hooks. |
| **CI** | Good | Format, lint, unit tests. |
| **Monorepo** | N/A | Single app. |

---

## 12) CI/CD & release engineering

| Area | Status | Notes |
|------|--------|------|
| **CI gates** | Good | Format, lint, mypy (non-blocking), unit tests. |
| **Build reproducibility** | Partial | No lockfile. |
| **Versioning** | Partial | pyproject version; no changelog process. |
| **Progressive delivery** | N/A | Single bot. |
| **Rollback** | Missing | No doc. |
| **Environment parity** | Partial | Config overrides; no drift doc. |

---

## 13) Documentation & knowledge capture

| Area | Status | Notes |
|------|--------|------|
| **ADRs** | Good | 001 (Phase 1), 002 (Phase 2). |
| **Onboarding** | Partial | README; no “first PR” playbook. |
| **Diagrams** | Partial | docs/assets diagram. |
| **API docs** | N/A | No REST API. |
| **Playbooks** | Missing | No “how to do X safely”. |

---

## 14) Governance & maintainability

| Area | Status | Notes |
|------|--------|------|
| **CODEOWNERS** | Missing | No ownership file. |
| **Module boundaries** | Missing | No lint/build constraints. |
| **Conventions** | Good | .cursor/rules. |
| **Tech debt register** | Missing | No prioritized list. |

---

## 15) UX & product quality

| Area | Status | Notes |
|------|--------|------|
| **Accessibility** | Partial | Streamlit dashboard (app/dashboard); no WCAG audit. |
| **i18n** | N/A | English-only. |
| **Latency budgets** | Missing | Not defined. |
| **UI state** | Partial | Dashboard has structure; loading/error/empty not formalized. |

---

## 16) Compliance & privacy

| Area | Status | Notes |
|------|--------|------|
| **PII mapping** | Missing | Mind file has conversational data. |
| **Encryption** | Partial | S3/HTTPS; no at-rest/key doc. |
| **Audit trails** | Missing | No “who did what when”. |
| **Consent/retention** | Missing | No GDPR/CCPA-style doc. |
| **Vendor risk** | Missing | No third-party review doc. |

---

# Phase 3 Plan: Modularization, Coverage & Lockfile, SCA

**Goal:** (1) Split the largest modules (message_event and/or message_bus) into smaller, focused modules; (2) add a lockfile and optional SCA in CI; (3) extend logging (print→logger) to more high-traffic modules; (4) optionally add coverage reporting and one runbook.

---

## 3.1 Modularization (message_event and message_bus)

- **Scope:** Start with one of the two; prefer **message_event** (smaller and more clearly separable by concern).
- **message_event.py:** Identify natural seams:
  - **Pre-message:** emotion decay, ethical conflict logging, term extraction (could move to a “message_prep” or “message_context” helper).
  - **Context building:** building internal_state, coparent/relationship checks (could live in a dedicated module or in a shared “context_builder” used by both event and bus).
  - **Post-response:** mood update, personality update, episodic memory, stream_of_consciousness, etc. (could become “message_post_processing” or similar).
- **Deliverable:** Split message_event into 2–4 modules under `app/events/` (e.g. `message_event.py` as thin orchestrator, `message_context.py`, `message_post.py`) with clear boundaries. Keep message_bus as-is for Phase 3 unless time permits a similar extraction (e.g. “context building” shared with message_event).
- **Risk:** Many optional integrations (try/import) and shared state; preserve behavior and test with manual or existing tests.

---

## 3.2 Lockfile and reproducible installs

- **Add pip-tools (pip-compile):** Add `pip-tools` to requirements-dev (or document in README). Generate `requirements.lock` (or `requirements.txt` from a `requirements.in`) so `pip install -r requirements.lock` is reproducible.
- **Option A:** Keep current `requirements.txt` as the “source” and run `pip-compile requirements.txt -o requirements.lock` (or use a `requirements.in` with unpinned deps and compile to `requirements.txt`).
- **Option B:** Document in README that “for reproducible installs run `pip-compile requirements.txt -o requirements.lock` and install from the lockfile.”
- **CI:** Optionally install from lockfile in CI if present; otherwise keep current CI behavior.

---

## 3.3 Dependency vulnerability scanning (SCA)

- **Add a security step to CI:** Use `pip-audit` or `safety` (or GitHub’s Dependabot alerts; no workflow change). Example: `pip install pip-audit && pip-audit` in CI. On failure, either fail the job or report (e.g. allow failure initially with a comment that findings must be triaged).
- **Deliverable:** One extra step in `.github/workflows/ci.yml` that runs SCA; document in README that dependency vulnerabilities are checked in CI.

---

## 3.4 Extend print→logger to more modules

- **Priority:** High-traffic or shared modules: e.g. `app/core/dinner/dinner_journal.py`, `app/services/response_service.py`, `app/core/knowledge.py`, `app/core/expansion.py`, `app/core/mood/mood_manager.py`. Replace `print()` with `get_logger(__name__)` and appropriate level; do not log tokens or secrets.
- **Scope:** Aim for 2–3 more modules (or one batch of 5–10 files) so that the remaining print count drops noticeably; document “use logger, not print” in project-conventions or python-style if not already.

---

## 3.5 Optional

- **Coverage in CI:** Run `pytest --cov=app --cov-report=term-missing` and either upload to a service or only print in the log. Do not enforce a coverage gate in Phase 3 unless desired.
- **One runbook:** Add `docs/runbooks/` with a single runbook, e.g. “Mind file not loading (S3/config)” or “Discord bot not responding,” with steps to check config, env, S3, and logs.
- **ADR 003:** Add `docs/adr/003-phase3-modularization-lockfile-sca.md` summarizing Phase 3 decisions.

---

## What Phase 3 deliberately does not do

- No full message_bus split (can be Phase 4).
- No layering enforcement or dependency inversion.
- No coverage gate or mandatory mypy pass (mypy can stay non-blocking).
- No formal mind-file schema or validation at boundaries.
- No PII/compliance documentation.
- No CODEOWNERS or tech-debt register.

---

## Suggested order of implementation

1. **Lockfile:** Add pip-tools, generate lockfile, document in README; optionally use in CI.
2. **SCA:** Add pip-audit (or safety) step to CI; document.
3. **Print→logger:** Extend to 2–3 high-traffic modules (dinner_journal, response_service, knowledge, expansion, mood_manager).
4. **Modularization:** Split message_event into orchestrator + 2–3 modules; update imports and run tests.
5. **Optional:** Coverage step in CI (report only); one runbook; ADR 003.

After Phase 3, re-audit and define Phase 4 (e.g. message_bus split, coverage gate, layering hints, onboarding playbook).
