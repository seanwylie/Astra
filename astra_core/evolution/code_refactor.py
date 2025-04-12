"""
code_refactor.py

Astra's self-evolution module: maps all uses of load_mind/save_mind,
identifies which modules touch which parts of the mind, and proposes
splits of mind_file.json into modular S3-stored components.

Phase 1: scan + suggest mind refactor layout
Phase 2: generate mind_manifest.json
"""

import os
import re
import json
from collections import defaultdict

# Configurable paths
PROJECT_ROOT = os.path.expanduser("~/astra_reflections")
IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv"}
MIND_KEYS = ["stored_knowledge", "self_reflections", "self_questions", "past_conversations", "emotional_state", "trust_levels"]
MIND_ACCESS_PATTERN = re.compile(r'mind_data\[\"(.*?)\"\]')

MIND_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "mind_manifest.json")
S3_BUCKET = "swylie-astra"
S3_BASE_PATH = "mind"

# Phase 1 — Map codebase mind interactions
def scan_codebase():
    usage_map = defaultdict(lambda: defaultdict(list))

    for dirpath, _, filenames in os.walk(PROJECT_ROOT):
        if any(ignored in dirpath for ignored in IGNORE_DIRS):
            continue

        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            full_path = os.path.join(dirpath, fname)
            with open(full_path, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if "load_mind" in line or "save_mind" in line:
                        usage_map[fname]["mind_calls"].append((lineno, line.strip()))
                    if "mind_data[" in line:
                        matches = MIND_ACCESS_PATTERN.findall(line)
                        for key in matches:
                            usage_map[fname][key].append((lineno, line.strip()))

    return usage_map


def suggest_modular_split(usage_map):
    print("\n🔍 Suggested Modular Mind Split:")
    split = defaultdict(set)

    for filename, sections in usage_map.items():
        for key in MIND_KEYS:
            if key in sections:
                split[key].add(filename)

    for key in MIND_KEYS:
        files = list(split[key])
        if files:
            print(f"\n🧠 '{key}' is used in:")
            for f in files:
                print(f"   - {f}")
        else:
            print(f"\n⚠️ '{key}' does not appear to be used anywhere.")


def generate_mind_manifest():
    manifest = {
        "version": "1.0",
        "modules": {
            key: f"s3://{S3_BUCKET}/{S3_BASE_PATH}/{key}.json"
            for key in MIND_KEYS if key != "trust_levels"  # Skip unused by default
        }
    }
    with open(MIND_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    print(f"\n📄 mind_manifest.json written to: {MIND_MANIFEST_PATH}")


if __name__ == "__main__":
    print("🧠 Scanning Astra's codebase for mind usage patterns...")
    usage_report = scan_codebase()
    suggest_modular_split(usage_report)
    generate_mind_manifest()
