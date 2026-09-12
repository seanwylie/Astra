# ADR 003: Phase 3 modularization, lockfile, and SCA

## Status

Accepted (implemented).

## Context

After Phase 2, the project had CI, structured logging in hot paths, and clearer exceptions. Remaining gaps: no lockfile for reproducible installs, no dependency vulnerability scanning, more `print()` usage in other modules, and a large “god” module (`message_event.py`) that mixed pre-send, send, and post-response logic.

## Decision

- **Lockfile**: Add `pip-tools` to `requirements-dev.txt`. Generate `requirements.lock` with `pip-compile requirements.txt -o requirements.lock`. Document in README: for reproducible installs use `pip install -r requirements.lock`; to regenerate run `pip-compile requirements.txt -o requirements.lock`. CI installs from `requirements.lock` when present.
- **SCA**: In CI, add a step after installing dependencies: run `pip-audit` (e.g. `pip-audit -r requirements.txt`). Job fails on vulnerabilities (or run with `continue-on-error` initially and triage). Document in README that dependency vulnerabilities are checked in CI via pip-audit.
- **Print to logger**: Replace `print()` with `get_logger(__name__)` and appropriate level (debug/info/warning/error) in: `app/core/dinner/dinner_journal.py`, `app/services/response_service.py`, `app/core/knowledge.py`, `app/core/expansion.py`, `app/core/mood/mood_manager.py`. Do not log tokens or secrets (see secrets-logging rule).
- **Message event split**: Keep `app/events/message_event.py` as a thin orchestrator. Add `app/events/message_post.py` containing all logic that runs *after* the response is sent: store conversation, awareness bus, mood, trust, personality, stream of consciousness, emotional autobiography, temporal self, self-model, episodic memory, relationship system, and full integration. Expose `run_post_response_updates(...)`. Move helpers used only for post-response (`_record_temporal_landmark_if_significant`, `_trigger_self_model_update_if_significant`, `_apply_full_integration`) into `message_post`. `handle_message` calls `run_post_response_updates` after sending the response; no change to external behavior.
- **Optional**: Add coverage reporting in CI (`pytest --cov=app --cov-report=term-missing`) without a coverage gate. Add runbook `docs/runbooks/mind-file-not-loading.md` for diagnosing mind load/save issues (config, env, S3, IAM, InfluenceError/ConfigurationError). Add this ADR.

## Consequences

- Reproducible installs via lockfile; CI and developers can align on exact dependency versions.
- Known vulnerabilities are surfaced by pip-audit in CI.
- Additional modules use structured logging instead of print, improving observability and consistency with secrets policy.
- `message_event.py` is smaller and focused on orchestration; post-response behavior is easier to test and change in `message_post.py`. Existing imports of `handle_message` from `app.events.message_event` continue to work.
