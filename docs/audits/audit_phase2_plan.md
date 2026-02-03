# Astra Codebase Audit (Post–Phase 1) and Phase 2 Plan

This document re-audits the codebase against the 16 categories after Phase 1, then proposes a concrete **Phase 2** plan.

---

## 1) Architecture & design sanity

| Area | Status | Notes |
|------|--------|------|
| **Modularization** | Partial | Phase 1 removed dead code. `app/events/message_event.py` (~1150 lines) and `app/core/messaging/message_bus.py` (~1660 lines) remain large; good candidates to split. |
| **Layering** | Weak | Core imports `app.config`, `app.interfaces`, `app.logging_config`. Domain is not isolated from config/infra. `utils/time_utils` still imports from `app`. |
| **API contracts** | N/A | No public REST API; Discord bot. Internal interfaces (e.g. `load_mind`/`save_mind`) are stable but undocumented. |
| **Cycles** | Unknown | No automated cycle detection. Many cross-imports between core/services/interfaces. |
| **Error handling** | Improved | Phase 1 updated error-handling rule (Astra-only). No `app/exceptions.py`; handling is ad hoc (try/except, log, continue or re-raise). |
| **Config** | Good | Single loader (`app.config.loader`), env overrides, validation rules. No single typed config object (e.g. dataclass). |
| **Deprecation** | Missing | No formal deprecation plan or migration docs. |

---

## 2) Reduce redundancy & complexity

| Area | Status | Notes |
|------|--------|------|
| **Dead code** | Improved | Phase 1 removed `discord_astra.py` (moved to maintenance/legacy), `utils/config_loader.py`. |
| **DRY** | Weak | Optional integration blocks (`try/import … _AVAILABLE`) duplicated in `message_event.py` and `message_bus.py`. Repeated `load_config("general_config")` in many files. |
| **Control flow** | Mixed | Deep nesting and long functions in message_event and message_bus. |
| **Primitive obsession** | Mixed | Many `dict`/`str` flows; some value types (e.g. mood, emotion) could be clearer. |
| **Duplicate data models** | Partial | Mind file shape implied; single load/save in `influence.py` + `SmartMindSession`. |
| **Patterns** | Ad hoc | Optional integrations via try/import flags; no shared “integration registry”. |

---

## 3) Code health & readability

| Area | Status | Notes |
|------|--------|------|
| **Naming** | Good | Generally consistent. Legacy comment "beta/events" in message_event. |
| **Style** | Good | Phase 1 added Makefile + pyproject.toml (black, isort, flake8, mypy). Rule matches tooling. |
| **Type safety** | Partial | Many return type hints; mypy config in pyproject. No CI type check. |
| **Docstrings** | Mixed | Present in many modules; large files need more “why” where non-obvious. |
| **Cleverness** | Low | Mostly straightforward; some broad `except Exception`. |
| **print()** | Poor | **328 `print()` calls in app/** (56 files). Should use `logger` for production paths; secrets rule says no tokens in logs. |

---

## 4) Testability & automated confidence

| Area | Status | Notes |
|------|--------|------|
| **Pyramid** | Partial | Phase 1 added pytest markers (`integration`/`unit`); two tests marked integration. |
| **Coverage** | Low | 9 test files; no coverage gates; no CI. |
| **Golden/snapshots** | None | No snapshot tests. |
| **Property-based** | None | No hypothesis or similar. |
| **Flake** | Unknown | conftest sets LOG_LEVEL; no explicit timeouts/isolation notes. |
| **Fixtures** | Minimal | conftest sets ASTRA_CONFIG_DIR/LOG_LEVEL; no shared mind/config factories. |

---

## 5) Security audit & hardening

| Area | Status | Notes |
|------|--------|------|
| **Threat model** | Missing | Not documented. |
| **SCA** | Missing | No dependency vulnerability scanning or CI. |
| **Secrets** | Good | .cursor rules + .gitignore; env for tokens. |
| **AuthN/AuthZ** | Minimal | Discord bot token; no RBAC in repo. |
| **Input validation** | Partial | Config validation; no formal schema for mind file or Discord input. |
| **Secure defaults** | N/A | No web server (Streamlit is optional dashboard). |
| **Security logging** | Partial | get_logger; no dedicated auth-failure or suspicious-pattern logging. |
| **Supply chain** | Partial | Pinned versions in requirements.txt; no lockfile (pip-compile); no signed builds. |

---

## 6) Performance audit & tuning

| Area | Status | Notes |
|------|--------|------|
| **Profiling** | None | No baseline profiling. |
| **Hot path** | Unknown | No algorithmic audit. |
| **DB** | N/A | No SQL DB; S3/JSON. |
| **Caching** | Partial | Config cached in loader; mind/session in memory. |
| **Concurrency** | Mixed | Async in places (message_bus, influence); sync in others. |
| **Batching/backpressure** | Unknown | No explicit strategy. |
| **Payload** | Unknown | No trimming/compression audit. |

---

## 7) Reliability, resilience & operability

| Area | Status | Notes |
|------|--------|------|
| **SLOs/SLIs** | Missing | Not defined. |
| **Timeouts/retries** | Partial | **mama_gpt** has configurable timeout + retries; **S3 and most OpenAI call sites have no timeout/retry**. |
| **Idempotency** | Undocumented | Mind save is effectively overwrite; no doc. |
| **Graceful degradation** | Good | Optional integrations use `*_AVAILABLE` flags. |
| **Chaos** | None | No fault injection. |
| **Runbooks** | Missing | No runbooks in repo. |
| **Postmortem** | Missing | No process doc. |

---

## 8) Observability & telemetry

| Area | Status | Notes |
|------|--------|------|
| **Structured logging** | Partial | get_logger; no correlation/request IDs. |
| **Metrics** | Partial | `app/core/prometheus_integration.py` exists; no dashboard/alerting docs. |
| **Tracing** | None | No distributed tracing. |
| **Dashboards** | Partial | Streamlit dashboard in app/dashboard; no ops dashboards doc. |
| **Alerts** | Missing | No alerting rules in repo. |

---

## 9) Data quality & correctness

| Area | Status | Notes |
|------|--------|------|
| **Schema** | Implicit | Mind file shape (self_reflections, self_questions, stored_knowledge) not formalized. |
| **Validation at boundaries** | Partial | Config validated; mind load/save has no schema validation. |
| **Backfills/repair** | Partial | maintenance/ scripts (mind_cleanse, etc.). |
| **Consistency** | Undocumented | No explicit eventual vs strong consistency. |
| **Retention/deletion** | Missing | No compliance doc. |

---

## 10) Dependencies & upgrades

| Area | Status | Notes |
|------|--------|------|
| **Version plan** | Partial | requirements.txt + pyproject.toml (Phase 1); versions pinned. |
| **Deprecated APIs** | Unknown | No audit. |
| **Abandonware** | Unknown | No audit. |
| **Lockfile** | Missing | No pip-compile or similar; no reproducible install artifact. |
| **Automated PRs** | Missing | No Dependabot/Renovate or CI dependency check. |

---

## 11) DevEx

| Area | Status | Notes |
|------|--------|------|
| **Bootstrap** | Partial | README + scripts/setup_venv.sh; no single “bootstrap” command. |
| **Scripts** | Good | Phase 1: Makefile (format, lint, test, test-unit). |
| **Pre-commit** | Missing | No pre-commit hooks. |
| **CI** | Missing | No GitHub Actions or other CI. |
| **Monorepo** | N/A | Single app; clear structure. |

---

## 12) CI/CD & release engineering

| Area | Status | Notes |
|------|--------|------|
| **CI gates** | Missing | No tests + lint + type checks in CI. |
| **Build reproducibility** | Partial | requirements + pyproject; no lockfile. |
| **Versioning** | Partial | pyproject version; no SemVer/changelog process. |
| **Progressive delivery** | N/A | Single bot; no canary. |
| **Rollback** | Missing | No documented rollback. |
| **Environment parity** | Partial | Config env overrides; no drift control doc. |

---

## 13) Documentation & knowledge capture

| Area | Status | Notes |
|------|--------|------|
| **ADRs** | Missing | No architecture decision records. |
| **Onboarding** | Partial | README; no “first PR” playbook. |
| **Diagrams** | Partial | docs/assets diagram; no maintained data-flow doc. |
| **API docs** | N/A | No REST API. |
| **Playbooks** | Missing | No “how to do X safely” playbooks. |

---

## 14) Governance & maintainability

| Area | Status | Notes |
|------|--------|------|
| **CODEOWNERS** | Missing | No code ownership file. |
| **Module boundaries** | Missing | No lint/build constraints. |
| **Conventions** | Good | .cursor/rules. |
| **Tech debt register** | Missing | No prioritized paydown list. |

---

## 15) UX & product quality

| Area | Status | Notes |
|------|--------|------|
| **Accessibility** | N/A | Discord bot; Streamlit dashboard exists (app/dashboard). |
| **i18n** | N/A | English-only. |
| **Latency budgets** | Missing | Not defined. |
| **UI state** | Partial | Dashboard has structure; no formal loading/error/empty doc. |

---

## 16) Compliance & privacy

| Area | Status | Notes |
|------|--------|------|
| **PII mapping** | Missing | Mind file has conversational data; no map. |
| **Encryption** | Partial | S3/HTTPS; no explicit at-rest/key doc. |
| **Audit trails** | Missing | No “who did what when” doc. |
| **Consent/retention** | Missing | No GDPR/CCPA-style doc. |
| **Vendor risk** | Missing | No third-party review doc. |

---

# Phase 2 Plan: CI/CD, Code Health, and Reliability Basics

**Goal:** Add minimal CI and pre-commit, reduce `print()` in critical paths in favor of logging, introduce a small `app/exceptions.py` and use it in a few key places, and add timeouts/retries for external calls (S3, OpenAI) where missing.

---

## 2.1 CI/CD and DevEx

- **GitHub Actions (or equivalent):** Add a single workflow that:
  - Runs on push/PR: `make format` check (or black/isort --check), `make lint` (flake8 + mypy), and `make test-unit` (pytest -m "not integration").
  - Uses a supported Python version (e.g. 3.10 or 3.11).
- **Pre-commit:** Add `.pre-commit-config.yaml` with:
  - black, isort (Python)
  - Optional: trailing whitespace, end-of-file fixer
  - Optional: secret scanning (e.g. detect-secrets or gitleaks)
- **README:** Document that CI runs on push/PR and that pre-commit can be installed with `pre-commit install`.

**Out of scope for Phase 2:** Coverage gates, security scanning in CI, lockfile (can be Phase 3).

---

## 2.2 Code health: logging and exceptions

- **Replace `print()` with `logger` in hot paths:** Focus on:
  - `app/events/message_event.py` (user-facing message flow)
  - `app/core/messaging/message_bus.py` (response generation)
  - `app/services/message_processing_service.py`
  - `app/main.py`
  Use `get_logger(__name__)` and appropriate levels (debug/info/warning/error). Do not log tokens or secrets (align with .cursor/rules/secrets-logging.mdc).
- **Introduce `app/exceptions.py`:** Define a small set:
  - Base: `AstraException`
  - Subclasses: e.g. `ConfigurationError`, `MindLoadError` (or `InfluenceError`), optional `ExternalServiceError`
  Use them in 2–3 key places: e.g. config loader (missing required key), influence (load_mind/save_mind on failure) so callers can catch specific errors. Update .cursor/rules/error-handling.mdc to reference `app.exceptions`.
- **Legacy comment:** Remove or update the "beta/events" comment in `message_event.py` to reflect current structure.

---

## 2.3 Reliability: timeouts and retries for external calls

- **S3 (influence.py):** Add a small wrapper or use botocore config for `read_timeout`/`connect_timeout` and retries (e.g. `max_attempts=3`, exponential backoff). Apply to sync `s3.get_object`/`put_object` and document that async aioboto3 calls should use equivalent config.
- **OpenAI:** Audit call sites (message_generator, mama_gpt, processing, question_answerer, etc.). Ensure:
  - Timeout is set (e.g. from config or a shared constant, 60–120s for completion).
  - Retries with backoff where appropriate (mama_gpt already has this; extend pattern to at least one other critical path, e.g. message_generator or response_service).
- **Document:** Add a short “Reliability” or “External calls” section in README or docs: timeouts and retries are used for S3 and OpenAI; idempotency of mind save (overwrite).

---

## 2.4 Optional (if time permits)

- **Shared test fixtures:** In `tests/conftest.py`, add a fixture that provides a minimal mind dict (e.g. `{"self_reflections": [], "self_questions": [], "stored_knowledge": []}`) and optionally a fixture that loads config so tests don’t depend on filesystem layout.
- **One ADR:** Add `docs/adr/001-phase1-foundation.md` summarizing Phase 1 (config consolidation, dead code, paths, DevEx) and `docs/adr/002-phase2-ci-health-reliability.md` for Phase 2.

---

## What Phase 2 deliberately does not do

- No splitting of message_event or message_bus into smaller modules (Phase 3).
- No layering enforcement or dependency inversion.
- No coverage gates or integration tests in CI.
- No lockfile or automated dependency PRs.
- No formal mind-file schema or validation at boundaries.
- No PII/compliance documentation.

---

## Suggested order of implementation

1. **app/exceptions.py** and use in config loader + influence (2–3 call sites); update error-handling rule.
2. **Replace print with logger** in message_event, message_bus, message_processing_service, main (batch by file).
3. **S3 timeouts/retries** in influence.py; **OpenAI timeout/retry** in one additional path (e.g. message_generator or response_service).
4. **Pre-commit config** and README note.
5. **GitHub Actions workflow** (format check, lint, test-unit).
6. **Short reliability doc** (README or docs).
7. Optional: conftest fixtures; one ADR.

After Phase 2, re-audit and define Phase 3 (e.g. modularization of message_event/message_bus, test coverage and fixtures, dependency lockfile and SCA).
