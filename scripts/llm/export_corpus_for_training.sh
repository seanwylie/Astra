#!/usr/bin/env bash
# Phase A3: Export Astra corpus for training the local model.
# Run this before training (e.g. weekly) so the model stays in sync with Astra's growth.
set -e
cd "$(dirname "$0")/.."
OUT="${1:-data/astra_corpus.jsonl}"
mkdir -p "$(dirname "$OUT")"
echo "Exporting corpus to $OUT ..."
PYTHONPATH=. .venv/bin/python -m app.core.evolution.corpus_export "$OUT"
echo ""
echo "Corpus written. Next steps for training (Phase A3):"
echo "  - Ollama: Use Ollama's fine-tune or import flow; then set OLLAMA_MODEL to the new model name."
echo "  - Generic: Use your LoRA/fine-tune tool with $OUT (JSONL: role, content, source, timestamp)."
echo "  - See docs/evolution.md §3 for details."
