#!/usr/bin/env python3
import json
import re
from pathlib import Path
from collections import defaultdict

FILE_STRUCTURE_PATH = Path(__file__).parent.parent / "file_structure.json"

def load_structure():
    try:
        with open(FILE_STRUCTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ file_structure.json not found. Run scan_file_structure.py first.")
        return []

def collect_function_usage(structure):
    all_defined = defaultdict(set)  # file → {funcs}
    all_used = set()

    for file in structure:
        path = file["path"]
        for func in file.get("functions", []):
            all_defined[path].add(func)

        for imp in file.get("imports", []):
            match = re.search(r"\.([a-zA-Z_][a-zA-Z0-9_]*)$", imp)
            if match:
                all_used.add(match.group(1))

        for use in file.get("uses", []):
            all_used.add(use)

    return all_defined, all_used

def detect_dead_functions(all_defined, all_used):
    dead_by_file = {}
    total_dead = 0

    for file, funcs in all_defined.items():
        dead_funcs = [f for f in funcs if f not in all_used and not f.startswith("__")]
        if dead_funcs:
            dead_by_file[file] = dead_funcs
            total_dead += len(dead_funcs)

    return dead_by_file, total_dead

def main():
    print("🧹 Running Dead Code Detector...")

    structure = load_structure()
    if not structure:
        return

    all_defined, all_used = collect_function_usage(structure)
    dead_by_file, total_dead = detect_dead_functions(all_defined, all_used)

    if not dead_by_file:
        print("✅ No dead functions found.")
        return

    print(f"\n🧠 Detected {total_dead} unused (dead) functions in {len(dead_by_file)} files:\n")

    for file, funcs in dead_by_file.items():
        print(f"📂 {file} → {len(funcs)} dead functions")
        for f in funcs:
            print(f"   - {f}")
        print()

if __name__ == "__main__":
    main()
