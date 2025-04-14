#!/usr/bin/env python3

import json
from pathlib import Path

def main():
    structure_path = Path(__file__).parent.parent / "file_structure.json"

    if not structure_path.exists():
        print("❌ file_structure.json not found. Please run scan_file_structure.py first.")
        return

    with open(structure_path, "r") as f:
        structure = json.load(f)

    all_files = set()
    referenced_files = set()

    for file in structure:
        path = file["path"]
        if path.endswith(".py") and "__init__" not in path:
            all_files.add(path)
        referenced_files.update(file.get("uses", []))

    unused_files = sorted(all_files - referenced_files)

    if not unused_files:
        print("✅ No unused files found.")
        return

    print("\n🧹 Potentially Unused Python Files:\n")
    for path in unused_files:
        print(f"  - {path}")

    output_path = Path(__file__).parent / "dead_files.json"
    with open(output_path, "w") as f:
        json.dump(unused_files, f, indent=2)
    print(f"\n💾 Saved report to: {output_path}")

if __name__ == "__main__":
    print("📦 Running Dead File Detector...")
    main()
