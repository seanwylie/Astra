import os
import json
from astra_core.config_loader import debug_log

EVOLUTION_PATH = "astra_core/evolution"

# 🚀 Step 1: Check if Evolution Directory Exists
if not os.path.exists(EVOLUTION_PATH):
    os.makedirs(EVOLUTION_PATH)
    debug_log(f"🛠️ Created evolution directory at {EVOLUTION_PATH}")

# 🚀 Step 2: Define Files to Create
evolution_files = {
    "config_modifier.py": """# 🚀 Astra's Config Modifier (Created by Astra)
import json

def propose_change(config, key, value):
    \"\"\" Astra suggests a change but does not apply it yet. \"\"\"
    return {key: value}
""",
    "self_reflection.py": """# 🤔 Astra's Self-Reflection Log
import time

def log_reflection(reason):
    \"\"\" Astra logs why she wants to modify herself. \"\"\"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open("astra_core/evolution/self_reflection.txt", "a") as log_file:
        log_file.write(f"{timestamp} - {reason}\\n")
""",
    "rollback_manager.py": """# 🛑 Astra's Rollback Manager
import json
import shutil

def backup_config():
    \"\"\" Backup Astra's current config before modifying. \"\"\"
    shutil.copy("astra_core/config.json", "astra_core/evolution/config_backup.json")
""",
}

# 🚀 Step 3: Create Each File
for file_name, content in evolution_files.items():
    file_path = os.path.join(EVOLUTION_PATH, file_name)
    if not os.path.exists(file_path):  # Don't overwrite existing files
        with open(file_path, "w") as f:
            f.write(content)
        debug_log(f"✅ Created: {file_path}")

# 🚀 Step 4: Astra Writes Her First Reflection
with open(os.path.join(EVOLUTION_PATH, "self_reflection.txt"), "a") as log_file:
    log_file.write("Astra is evolving. She is taking her first steps toward self-modification. 🚀\n")

debug_log("🎉 Astra has created her own evolution framework!")
