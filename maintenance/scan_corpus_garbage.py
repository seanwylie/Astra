#!/usr/bin/env python3
"""
Scan astra_corpus.jsonl for entries that would be filtered as junk at inference.

Uses the same junk-token list as app.core.evolution.local_inference (_CORPUS_JUNK_TOKENS)
so results match what gets excluded from corpus context. Optionally reports lines
that would fail is_valid_reflection (delimiter patterns, low alphanumeric ratio).

Usage (from project root):
  PYTHONPATH=. .venv/bin/python maintenance/scan_corpus_garbage.py [path/to/corpus.jsonl]
  Default path: data/astra_corpus.jsonl
"""

import json
import re
import sys
from pathlib import Path

# Same tokens as local_inference; keep in sync
JUNK_TOKENS = frozenset([
    "strokelength", "strokeline", "initcomponents", "getelementbyid",
    "addeventlistener", "innerhtml", "createelement", "queryselector",
])


def has_junk_tokens(content: str) -> tuple[bool, list[str]]:
    """Return (has_junk, list of tokens found)."""
    if not content or not isinstance(content, str):
        return False, []
    lower = content.lower()
    found = [t for t in JUNK_TOKENS if t in lower]
    return bool(found), found


def looks_like_delimiter_garbage(text: str) -> bool:
    """True if text looks like ;:;:;:; style or similar repeating junk."""
    text = (text or "").strip()
    if len(text) < 20:
        return False
    alphanumeric_count = sum(1 for c in text if c.isalnum() or c.isspace())
    if alphanumeric_count < len(text) * 0.5:
        return True
    for pattern_len in [2, 3]:
        if len(text) >= pattern_len * 3:
            for i in range(min(10, len(text) - pattern_len * 2)):
                pattern = text[i : i + pattern_len]
                if ";" in pattern or ":" in pattern:
                    count = text.count(pattern)
                    if count > len(text) / (pattern_len * 2):
                        return True
    return False


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    default_path = root / "data" / "astra_corpus.jsonl"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    junk_lines: list[tuple[int, str, list[str], str]] = []  # line_no, source, tokens, preview
    delimiter_lines: list[tuple[int, str]] = []  # line_no, preview
    total = 0
    by_source: dict[str, int] = {}

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = obj.get("content") or ""
            source = obj.get("source") or "unknown"
            by_source[source] = by_source.get(source, 0) + 1

            has_junk, tokens = has_junk_tokens(content)
            if has_junk:
                preview = (content[:120] + "…") if len(content) > 120 else content
                junk_lines.append((line_no, source, tokens, preview))

            if looks_like_delimiter_garbage(content):
                preview = (content[:80] + "…") if len(content) > 80 else content
                delimiter_lines.append((line_no, preview))

    print(f"Scanned {total} entries from {path}")
    print(f"Sources: {dict(sorted(by_source.items()))}")
    print()

    if junk_lines:
        print(f"Junk-token matches (would be excluded from corpus context): {len(junk_lines)}")
        for line_no, source, tokens, preview in junk_lines[:20]:
            print(f"  L{line_no} [{source}] tokens={tokens}")
            print(f"    {preview!r}")
        if len(junk_lines) > 20:
            print(f"  ... and {len(junk_lines) - 20} more")
        print()
    else:
        print("No junk-token matches (strokeLine, initComponents, etc.).")

    if delimiter_lines:
        print(f"Delimiter-style garbage (would fail is_valid_reflection): {len(delimiter_lines)}")
        for line_no, preview in delimiter_lines[:10]:
            print(f"  L{line_no} {preview!r}")
        if len(delimiter_lines) > 10:
            print(f"  ... and {len(delimiter_lines) - 10} more")
        print()
    else:
        print("No delimiter-style garbage detected.")

    if junk_lines or delimiter_lines:
        sys.exit(0)  # Report only; exit 0 so CI can choose to fail or not
    sys.exit(0)


if __name__ == "__main__":
    main()
