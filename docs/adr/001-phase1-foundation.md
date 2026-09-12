# ADR 001: Phase 1 foundation (config, dead code, paths, DevEx)

## Status

Accepted (implemented).

## Context

The codebase had two config loaders, hardcoded paths, dead/legacy code, and no standard way to run format/lint. This made onboarding and consistency harder.

## Decision

- **Single config source**: Use only `app.config.loader`; remove `utils/config_loader.py` (legacy, wrong path).
- **Paths**: Remove hardcoded `/home/...` from `app.interfaces.influence` and `app.core.mood.mood_manager`; use config/env. Config JSON defaults use relative paths (`mind_file.json`, `data/astra_logs.json`).
- **Dead code**: Move `app/core/discord_astra.py` to `maintenance/legacy/`; update `config/doctor_config.json`. Deduplicate constants and remove unnecessary `sys.path` in `app/core/processing.py`.
- **DevEx**: Add `pyproject.toml` (deps, black/isort/mypy/pytest config) and `Makefile` (format, lint, test, test-unit). Update README and project-conventions rule.

## Consequences

- One place to load config; env overrides work consistently.
- No machine-specific paths in repo defaults.
- Format and lint are runnable via `make format` and `make lint`.
- Stale Cursor rules (questrade, database-changes, error-handling referencing non-existent exceptions) were updated or removed.
