# Astra

An experimental Discord-resident entity that is *raised* rather than programmed: personality
modes, a structured ethics core called the Spark, scheduled reflection ("Dinner Time"), and a
mind file that accumulates questions, knowledge, and self-reflections.

This repository is the **engine**. It ships a small synthetic mind under `fixtures/` so anyone
can install and test it. It does not ship a live personality, a conversation corpus, or
operator credentials.

**Experimental software, released for study and adaptation. Maintained as time permits. No
production-support commitment.**

Created by Sean Wylie and released as an open-source experiment through Wise Kids Studios.

## What it does

| Area | What is real |
| --- | --- |
| Personality modes | Six named styles that change tone and curiosity |
| Spark ethics | Structured values interviews that the entity has to reconcile |
| Dinner Time | A scheduled pause when emotion or ethics spike |
| Emotion engine | Intensity tracking, decay, and mood |
| Developmental stage | One canonical stage; advancement is intentional, not automatic |
| Memory | Local SQLite by default; optional S3 sync if you configure a bucket |
| Discord bot | Optional. Requires your token and a channel ID |

S3 is **opt-in**. An empty `s3_bucket` and `s3_sync_enabled: false` (the shipped defaults) mean
Astra does not talk to AWS.

## Prove it in five minutes

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/). Initial dependency
installation needs network. After that, the unit suite needs no Discord token,
OpenAI key, AWS account, or configuration.

```sh
uv sync --group dev
uv run pytest -q -m "not integration"
```

`pip install -r requirements.txt -r requirements-dev.txt` still works if you prefer a venv.

Semantic question-categorization needs the optional embeddings extra (`uv sync --extra embeddings`), which pulls torch. The unit suite does not.

That run uses `fixtures/example_mind.json` and a throwaway database under `tests/`. It should
not read or write a live mind.

To look at state without Discord:

```sh
PYTHONPATH=. streamlit run app/dashboard/app.py --server.port 8502
```

## Running the bot

Copy `.env.example` to `.env` and set `TOKEN` and `OPENAI_API_KEY`. Set
`DISCORD_CHANNEL_ID` (or put it in `config/discord_config.json`). AWS keys are required only
if you turn S3 sync on.

```sh
source .venv/bin/activate
PYTHONPATH=. python -m app.main
```

A systemd user unit is optional; see `scripts/install_astra_service.sh`. To pause it:

```sh
systemctl --user stop astra && systemctl --user disable astra
```

## Configuration

JSON files live in `config/`. Environment variables override the ones that differ per machine:

| Variable | Overrides |
| --- | --- |
| `DISCORD_CHANNEL_ID` | Discord channel |
| `ASTRA_MIND_FILE` | Local mind file path (defaults to the example fixture) |
| `ASTRA_DB_PATH` | SQLite path |
| `S3_BUCKET_NAME` | Optional remote bucket |
| `ASTRA_CONFIG_DIR` | Alternate config directory |
| `LOG_LEVEL` | Logging verbosity |

Do not commit `.env`, `data/`, `logs/`, or a live `mind_file.json`.

## Honest limits

- The Discord bot needs a model API key. There is no offline conversation path yet.
- Thirteen test files cover a large tree; hermetic coverage is thinner than the line count.
- black, isort, and flake8 are configured but not CI gates. The current tree has
  thousands of pre-existing lint findings; do not treat a local `make lint` failure
  as a regression from this release.
- Optional S3 sync exists for operators who want it. It is off by default and must be given a
  bucket name before it does anything.
- The shipped Spark and shimmer files are synthetic fixtures, not a live interview.

## License

Apache-2.0. See `LICENSE` and `NOTICE`.

Security reports: see `SECURITY.md`. Please do not open a public issue for a vulnerability.
