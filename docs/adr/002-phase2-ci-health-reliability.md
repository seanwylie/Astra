# ADR 002: Phase 2 CI, code health, and reliability

## Status

Accepted (implemented).

## Context

After Phase 1, the project had no CI, many `print()` calls in hot paths, no project-specific exceptions, and no timeouts/retries on some external calls (S3, OpenAI).

## Decision

- **Exceptions**: Introduce `app.exceptions` (`AstraException`, `ConfigurationError`, `InfluenceError`, `ExternalServiceError`). Use in config loader (raise `ConfigurationError` on validation failure) and influence (raise `InfluenceError` on load/save failure). Update error-handling rule.
- **Logging**: Replace `print()` with `logger` in `app/events/message_event.py`, `app/core/messaging/message_bus.py`, `app/services/message_processing_service.py`, and `app/core/message_generator.py`. Fix legacy comment in message_event.
- **Reliability**: S3 client in `app.interfaces.influence` uses botocore `Config` (connect_timeout, read_timeout, retries). OpenAI client in `MessageGenerator` uses `timeout=60.0`. Document in README that S3 and OpenAI use timeouts/retries and mind save is idempotent.
- **CI**: Add `.github/workflows/ci.yml` (format check, flake8, mypy, unit tests with `-m "not integration"`). Add `.pre-commit-config.yaml` (black, isort, trailing-whitespace, end-of-file-fixer). Document pre-commit and CI in README.
- **Optional**: Add `minimal_mind_dict` fixture in `tests/conftest.py`. Add ADRs 001 and 002.

## Consequences

- Callers can catch `ConfigurationError` and `InfluenceError` for clearer handling.
- Production paths use structured logging instead of print.
- External calls are less likely to hang; retries improve resilience.
- CI and pre-commit keep format and lint consistent; unit tests run on push/PR.
