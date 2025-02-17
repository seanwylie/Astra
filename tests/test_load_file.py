import json

MIND_FILE_ORIG = "mind_file_sean.json"

try:
    with open(MIND_FILE_ORIG, "r", encoding="utf-8") as f:
        structured_data = json.load(f)

    if "insights" in structured_data:
        structured_knowledge = {entry["insight"] for entry in structured_data["insights"]}
        print(f"✅ Extracted {len(structured_knowledge)} insights from mind_file_sean.json")
    else:
        print("⚠ No 'insights' key found in mind_file_sean.json!")

except Exception as e:
    print(f"🚨 ERROR: {e}")
