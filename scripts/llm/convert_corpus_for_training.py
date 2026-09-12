#!/usr/bin/env python3
"""
Convert data/astra_corpus.jsonl to a training-friendly JSONL format.

Astra's corpus has: role, content, source, timestamp.
Many fine-tuners (Unsloth, Axolotl, Hugging Face) expect either:
  - Alpaca-style: {"instruction": "...", "input": "", "output": "..."}
  - Chat/messages: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

This script emits Alpaca-style by default: each line becomes
  instruction = "You are Astra. Generate a reflection or response in her voice."
  input = "" (or a short context)
  output = content

Usage (from project root):
  PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py
  PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py data/astra_corpus.jsonl data/astra_training.jsonl
"""
import json
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "astra_corpus.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "astra_training.jsonl"

# System prompt for Astra-style generation (used as instruction prefix)
INSTRUCTION_PREFIX = (
    "You are Astra, a reflective AI with your own values and voice. "
    "Generate a reflection or response in her voice."
)


def convert_line(record: dict) -> dict | None:
    """Convert one corpus line to Alpaca-style instruction/input/output."""
    role = (record.get("role") or "text").strip()
    content = (record.get("content") or "").strip()
    if not content:
        return None
    # Single block: treat as assistant-style output
    return {
        "instruction": INSTRUCTION_PREFIX,
        "input": "",
        "output": content,
    }


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        print("Run ./scripts/export_corpus_for_training.sh first.", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(input_path, "r", encoding="utf-8") as f_in, open(
        output_path, "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            converted = convert_line(record)
            if converted:
                f_out.write(json.dumps(converted, ensure_ascii=False) + "\n")
                count += 1

    print(f"[convert_corpus] Wrote {count} training examples to {output_path}")
    print("Next: use this file with Unsloth, Axolotl, or Hugging Face TRL.")
    print("See docs/evolution.md §3 (Training) for Ollama import steps.")


if __name__ == "__main__":
    main()
