# Astra Evolution

How Astra can evolve: corpus export, local inference, Astra-grown tools, and code change proposals.

**Full model update runbook (export → train → merge → deploy):** see **[docs/astra_model_update_guide.md](astra_model_update_guide.md)** for the step-by-step from corpus export through Unsloth training, weight merge, server transfer, Ollama ingestion, and personality layering.

## Phase A: What’s done vs remaining

| Step | Deliverable | Status | Remaining |
|------|-------------|--------|-----------|
| **A1** | Corpus export pipeline (mind, dinner, self_model, learning queue → JSONL) | ✅ Implemented | None. Run: `PYTHONPATH=. .venv/bin/python -m app.core.evolution.corpus_export` |
| **A2** | Local inference with corpus-as-context (Ollama-compatible) | ✅ Implemented | None. Set `OLLAMA_BASE_URL` (and optional `OLLAMA_MODEL`). |
| **A3** | Train/update local model on corpus; document how to run (e.g. weekly) | ✅ Script + doc | Run `./scripts/export_corpus_for_training.sh`; then run your training (Ollama/LoRA). See §3. |
| **A4** | Point inference at trained model | ✅ Config-only | Set `OLLAMA_MODEL` to your trained model name after A3. |

**Phase A remaining (concrete):** Run the steps in **Polish off Phase A and D1** below (export once; optionally set `OLLAMA_BASE_URL` and test; set `OLLAMA_MODEL` after training).

---

## D1: What’s done vs remaining

| Item | Status | Notes |
|------|--------|--------|
| Dream: try local model first, then OpenAI | ✅ Implemented | `app/core/astra_schedule/dream.py` |
| School (deepen reflection): try local model first, then OpenAI | ✅ Implemented | `app/core/processing.py` → `query_openai_for_deeper_thought` |
| Other reflection paths (play, dinner, message reply, etc.) | Not in scope | Plan says “e.g. school reflection, dream”; extend later if desired. |

**D1 remaining (concrete):**

1. **Verify:** With `OLLAMA_BASE_URL` set and a model running, trigger a dream and a school cycle and confirm logs show local inference (or fallback to OpenAI if the call fails).
2. **Optional:** Add more “inner voice” call paths (e.g. play, dinner reflection) to try local first; not required for D1.

---

## Polish off Phase A and D1 (run these)

From the **project root** (e.g. `cd /home/sean/dev/systems/Astra`):

**1. Phase A1 + A3 — Export corpus (once, or weekly before retraining)**

```bash
./scripts/export_corpus_for_training.sh
```

- Writes `data/astra_corpus.jsonl`. If mind/dinner/self_model aren't available yet, you may see fewer lines; that's fine.
- When you're ready to train a local model, run this again and then use §3 (Ollama/LoRA) to train on that file.

**2. Phase A2 + D1 — Local inference (optional but recommended)**

- **2a.** In `.env`, add (if you have Ollama running locally):

  ```bash
  OLLAMA_BASE_URL=http://localhost:11434
  # OLLAMA_MODEL=llama3.2   # optional; default is llama3.2
  ```

- **2b.** Quick test that local inference is available (no need to run the full bot):

  ```bash
  PYTHONPATH=. .venv/bin/python scripts/test_local_inference.py
  ```

- **2c.** With Astra running, trigger a dream or wait for a school cycle. In logs, look for `Dream reflection (local)` or local inference in school; if the local call fails, you'll see fallback to OpenAI.

**3. Phase A4 — Use a trained model (when you have one)**

- After you've trained/imported a model (see §3), set in `.env`:

  ```bash
  OLLAMA_MODEL=your-trained-model-name
  ```

No code changes needed; dream and school will use that model when local inference is available.

---

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
- **Usage:** Dream seed processing and school reflection (deepen-thought) both try the local model first when `OLLAMA_BASE_URL` is set; they fall back to OpenAI if disabled or if the call fails.

To use a **trained** model: train or import your model into Ollama (or your stack), then set `OLLAMA_MODEL` to that model name. No code change needed.

## 3. Training the local model (Phase A3)

Corpus is in `data/astra_corpus.jsonl`. Training is an offline step and depends on your setup.

### Step 1: Export the corpus (run before training, e.g. weekly)

```bash
./scripts/export_corpus_for_training.sh
# Writes data/astra_corpus.jsonl (role, content, source, timestamp per line)
```

### Step 2: Convert to a training format (optional but recommended)

Many fine-tuning tools expect **instruction/input/output** (Alpaca-style) or **messages**. A converter is included:

```bash
PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py
# Reads data/astra_corpus.jsonl, writes data/astra_training.jsonl (instruction, input, output)
```

You can then point Unsloth, Axolotl, or Hugging Face TRL at `data/astra_training.jsonl`.

### Step 3: Fine-tune (choose one path)

**Option A — Unsloth (recommended for ease, GPU needed)**
1. Install Unsloth (see [docs.unsloth.ai](https://docs.unsloth.ai)).
2. Use `data/astra_training.jsonl` (or convert to the dataset format Unsloth expects; see their Datasets Guide).
3. Fine-tune a base model (e.g. Llama 3.2, Mistral) with LoRA.
4. Export the adapter (e.g. Safetensors) or export to GGUF.

**Option B — Hugging Face TRL / PEFT**
1. Load `data/astra_training.jsonl` (or the raw corpus and map to `instruction`/`output` in code).
2. Fine-tune with LoRA; save the adapter.

**Option C — Other (Axolotl, llama.cpp fine-tune, etc.)**
Use your preferred tool. Corpus format: one JSON object per line with `role`, `content`, `source`, `timestamp`. Filter or weight by `source` (e.g. more weight on `dinner_journal`, `self_model`) if desired.

### Step 4: Import into Ollama and use

After you have a **LoRA adapter** (e.g. Safetensors) or a **GGUF** file:

1. **Using an adapter:** Create a Modelfile (e.g. `Modelfile.astra`):

   ```
   FROM llama3.2
   ADAPTER /path/to/your/adapter_directory
   ```

   Then: `ollama create astra -f Modelfile.astra`

2. **Using a GGUF:** If you exported a full model as GGUF, use `ollama create` with a Modelfile that references it (see [Ollama import docs](https://github.com/ollama/ollama/blob/main/docs/import.md)).

3. **Use the new model:** In `.env` set `OLLAMA_MODEL=astra` (or whatever name you gave). Dream and school will use it when local inference is available.

### Summary

| Step | Command / action |
|------|------------------|
| 1. Export corpus | `./scripts/export_corpus_for_training.sh` |
| 2. Convert for training | `PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py` |
| 3. Fine-tune | Unsloth / TRL / Axolotl on `data/astra_training.jsonl` (or raw corpus); export adapter or GGUF |
| 4. Import to Ollama | `ollama create astra -f Modelfile` (adapter or GGUF) |
| 5. Use in Astra | Set `OLLAMA_MODEL=astra` in `.env` |

Run the export (and optionally convert) periodically (e.g. weekly) before retraining so the model stays in sync with Astra's growth.

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
