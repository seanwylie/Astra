# Astra Evolution

How Astra can evolve: corpus export, local inference, Astra-grown tools, and code change proposals.

## 1. Corpus export (Phase A1)

Export Astra's mind, dinner journal, self-model, and learning queue to a single JSONL corpus for training or context.

```bash
PYTHONPATH=. .venv/bin/python -m app.core.evolution.corpus_export
# Writes data/astra_corpus.jsonl (create data/ if needed)
```

Optional output path:

```bash
PYTHONPATH=. .venv/bin/python -m app.core.evolution.corpus_export /path/to/corpus.jsonl
```

Schema: one JSON object per line with `role`, `content`, `source`, `timestamp`.

## 2. Local inference (Phase A2, A4)

When a local model (e.g. Ollama) is available, Astra can use it for reflection/dream with corpus-as-context.

- **Env vars:** `OLLAMA_BASE_URL` (e.g. `http://localhost:11434`), optional `OLLAMA_MODEL` (default `llama3.2`).
- **Config:** In `general_config.json`: `local_model_base_url`, `local_model_name`.
- **Usage:** Dream seed processing tries local model first when `OLLAMA_BASE_URL` is set; falls back to OpenAI if disabled or if the call fails.

To use a **trained** model: train or import your model into Ollama (or your stack), then set `OLLAMA_MODEL` to that model name. No code change needed.

## 3. Training the local model (Phase A3)

Corpus is in `data/astra_corpus.jsonl`. Training is an offline step and depends on your setup.

- **Ollama:** Use Ollama’s fine-tuning or import flow for your base model; point `OLLAMA_MODEL` to the new model name.
- **Generic:** Export corpus (above), then use your preferred tool (e.g. LoRA, fine-tune script) with the JSONL. Each line is `{"role": "...", "content": "...", "source": "...", "timestamp": "..."}`. Filter or weight by `source` if desired (e.g. more weight on `dinner_journal`, `self_model`).

Run corpus export periodically (e.g. weekly) before retraining so the model stays in sync with Astra’s growth.

## 4. Astra-grown tools (Phase B)

- **Registry:** `app/core/evolution/tool_registry.json` lists active tools (name, script_path, description, allowed_ops).
- **Sandbox:** Scripts run under `app/core/evolution/sandbox/` only; network is disabled unless the tool’s `allowed_ops` includes `network` or `ping`.
- **Approval:** New tools are added as *pending*. Co-parent uses Discord:
  - `!pending_tools` — list pending
  - `!approve_tool <name>` — approve and activate
  - `!reject_tool <name>` — remove from pending
- **Run:** `!run_tool <name> [args...]` (e.g. `!run_tool echo_astra hello`).
- **Propose (manual):** `!propose_tool <concept>` — LLM generates a script for that concept and adds it as pending.
- **Propose (automatic):** When Astra learns a concept in the trigger set (e.g. ping, time, date), a tool may be proposed automatically and added to pending.

## 5. Read own code and propose changes (Phase C)

- **Allowlisted paths:** Astra can only read paths in the allowlist (see `app/core/evolution/readable_code.py`). Default: `app/core/evolution/sandbox/`, `app/core/evolution/tool_registry.json`, `app/core/evolution/pending_tools.json`, `config/schedule_config.json`. Override with `evolution_readable_paths` in `general_config.json`.
- **Proposals:** Astra (or co-parent) can propose a code change:
  - `!propose_change <file_path> <goal>` — e.g. `!propose_change app/core/evolution/sandbox/echo_astra.py add a greeting`
- **Review:** Co-parent uses:
  - `!pending_proposals` — list pending code proposals
  - `!approve_proposal <index>` — apply the proposal and mark approved
  - `!reject_proposal <index>` — mark rejected
- **Audit:** Applied proposals are logged to `app/core/evolution/proposal_audit.log`.

## 6. Summary of commands

| Command | Description |
|--------|-------------|
| `!tools` | List active tools |
| `!pending_tools` | List tools awaiting approval |
| `!approve_tool <name>` | Approve a pending tool |
| `!reject_tool <name>` | Reject a pending tool |
| `!run_tool <name> [args...]` | Run an active tool |
| `!propose_tool <concept>` | Propose a new tool for a concept |
| `!pending_proposals` | List pending code change proposals |
| `!approve_proposal <index>` | Apply a code proposal |
| `!reject_proposal <index>` | Reject a code proposal |
| `!propose_change <file_path> <goal>` | Propose a code change (file must be allowlisted) |
