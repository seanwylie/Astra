# Contributing

Thanks for looking. Please read the next paragraph before investing effort.

This is an experimental research system, released so the approach and the code can be studied
and adapted. It is **maintained as time permits, with no production-support commitment**. Issues
and pull requests are welcome, but may not be reviewed promptly, and large unsolicited changes
are unlikely to be merged. If you need this to move at your pace, forking is a legitimate and
expected outcome.

## Getting set up

```sh
uv sync --group dev
uv run pytest -q -m "not integration"
```

The unit suite should need no Discord token, no OpenAI key, and no AWS account. It uses the
synthetic mind under `fixtures/` and a throwaway SQLite file under `tests/`.

If the suite requires network or a personal credential on a clean machine, that is a bug.

## What is likely to be accepted

- Bug fixes with a test that fails before the change and passes after
- Corrections to documentation that overstates what the code does
- Hermetic tests that replace a live S3 or Discord dependency
- Portability fixes for local-only operation

## What is unlikely to be accepted

- Shipping a live mind, conversation corpus, or operator identity
- New autonomy that posts to Discord or writes to S3 without an explicit opt-in
- Adding a dependency for something the standard library already does adequately
- Broad personality or ethics redesigns without a failing test that names the defect

## Conventions that matter

**Local is the default.** S3 and Discord are optional integrations. A missing bucket name means
do not talk to S3.

**Do not commit secrets or minds.** `.env`, `data/`, `logs/`, and live `mind_file.json` are
gitignored on purpose.
