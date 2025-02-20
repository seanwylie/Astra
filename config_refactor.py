import os
import json
import re

CONFIG_FILES = {
    "general": "config/general_config.json",
    "mood": "config/mood_config.json",
    "trust": "config/trust_config.json",
    "responses": "config/responses_config.json",
    "events": "config/event_triggers.json"
}

# Load existing configs
configs = {}
for key, path in CONFIG_FILES.items():
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            configs[key] = json.load(f)
    else:
        configs[key] = {}

# Regex patterns to identify hardcoded values
PATTERNS = {
    "mood_responses": r'"(I\'m feeling curious|I\'m feeling neutral|I\'m feeling excited|I\'m feeling thoughtful|I\'m feeling frustrated)"',
    "trust_levels": r'([+-]?\d*\.\d+|\d+)',  # Matches numeric values (trust thresholds, delays, decay factors)
    "state_responses": r'"(I\'m off to school|Time to wind down for the night|I\'m up, I\'m up, geez)"',
    "event_triggers": r'"(Time to reflect|Let’s explore this further!)"'
}

# Directory containing Astra's code
CODE_DIR = "astra_core"

# Function to replace hardcoded values
def replace_hardcoded_values(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for category, pattern in PATTERNS.items():
        matches = re.findall(pattern, content)
        for match in matches:
            replacement = f'configs["{category.split("_")[0]}"]["{category}"].get("{match}", "{match}")'
            content = content.replace(f'"{match}"', replacement)
            print(f"✅ Replaced {match} in {file_path}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# Recursively find all Python files in Astra's core directory
for root, _, files in os.walk(CODE_DIR):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            replace_hardcoded_values(file_path)

print("🎉 Refactoring complete! Astra is now fully config-driven.")
