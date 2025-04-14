#!/usr/bin/env python3
import json
from pathlib import Path

SCAN_PATH = Path(__file__).parent.parent / "file_structure.json"

def load_scan_data():
    if not SCAN_PATH.exists():
        print("❌ file_structure.json not found. Run scan_file_structure.py first.")
        return []
    with open(SCAN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_refactor_risk(file_entry):
    """Compute a simple refactor risk score based on heuristics."""
    score = 0

    # Heuristics
    if file_entry["line_count"] > 300:
        score += 2
    elif file_entry["line_count"] > 150:
        score += 1

    if file_entry["comment_ratio"] < 0.05:
        score += 1

    if len(file_entry["functions"]) > 10:
        score += 1

    if file_entry["likely_entrypoint"]:
        score += 2

    if not file_entry["has_test_file"]:
        score += 1

    if file_entry["layer"] == "unknown":
        score += 1

    return score

def update_scan_data(entries):
    updated = []
    for entry in entries:
        score = calculate_refactor_risk(entry)
        entry["refactor_risk_score"] = score
        updated.append(entry)
    return updated

def save_scan_data(entries):
    with open(SCAN_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    print(f"✅ Updated file_structure.json with refactor risk scores.")

def main():
    print("🛠️ Running Refactor Reporter...")
    data = load_scan_data()
    if not data:
        return
    updated = update_scan_data(data)
    save_scan_data(updated)

if __name__ == "__main__":
    main()
