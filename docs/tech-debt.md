# Tech debt register

A lightweight list of known technical debt items from the post-Phase 3 audit. Items are not formally prioritized here; use for planning and Phase 5+ work.

## Modularization and structure

- **message_bus still large after context extraction** (Phase 4): Context-building was moved to `context_builders.py`; message_bus remains the largest single module. Further splitting (e.g. by integration or reply path) could be considered.
- **Core imports config/interfaces everywhere (layering)**: No enforced dependency direction; `app/core` has many imports from config, interfaces, and utils. Consider documenting or enforcing layering (e.g. core → interfaces, no core ← config in hot path).

## Logging and code health

- **Remaining print() calls**: ~185 print() calls remain across 49 files (post Phase 4 batch 2). Continue replacing with logger in high-traffic and error paths; see project-conventions or python-style for “use logger, not print.”

## Quality and tooling

- **No automated cycle detection**: Import cycles are not checked in CI. Run `scripts/check_import_cycles.py` periodically; Phase 4 findings are in docs/audits/import-cycles-phase4.md (3 cycles found, including one large core cycle).
- **mypy non-blocking**: Mypy runs in CI with `|| true`; type errors do not fail the build. Consider fixing critical errors and turning mypy into a gate.
- **No coverage gate**: Coverage is reported in CI but not enforced. Optional: set a minimum coverage threshold.

## Data and boundaries

- **No mind-file schema**: Mind file shape is implicit. Consider a schema (e.g. JSON Schema or Pydantic) and validation at load/save boundaries.
- **No formal deprecation plan**: No documented process for deprecating APIs or config keys.

## Governance and docs

- **No CODEOWNERS**: No ownership file in the repo. Listed as tech debt only; adding CODEOWNERS is optional.
- **No threat model / PII mapping**: Security threat model and PII handling (e.g. mind/conversation data) are not documented.

---

*Last updated from Phase 4 audit. Revisit after Phase 5.*
