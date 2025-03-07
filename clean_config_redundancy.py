import os
import json
import logging
from collections import defaultdict

# ✅ Setup Logging
LOG_DIR = os.path.expanduser("~/astra_logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "config_check.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

CONFIG_DIR = os.path.expanduser("~/astra_reflections/astra_core/config")

def load_configs():
    """Load all JSON config files and track any corrupted ones."""
    configs = {}
    logging.info("🔍 Loading config files...")

    for file in os.listdir(CONFIG_DIR):
        if file.endswith(".json"):
            file_path = os.path.join(CONFIG_DIR, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    configs[file] = json.load(f)
                    logging.info(f"✅ Loaded: {file}")
            except json.JSONDecodeError:
                logging.error(f"❌ Skipping corrupted file: {file}")
                print(f"❌ Skipping corrupted file: {file}")

    logging.info(f"📊 Total config files loaded: {len(configs)}")
    return configs

def check_redundancy(configs):
    """Check for duplicate keys across config files and log them."""
    key_usage = defaultdict(list)
    total_keys = 0

    for file, config in configs.items():
        for key in config.keys():
            key_usage[key].append(file)
            total_keys += 1

    logging.info(f"📊 Scanned {total_keys} keys across {len(configs)} config files.")

    print("\n🔍 **Checking for redundant keys across configs...**")
    for key, files in key_usage.items():
        if len(files) > 1:
            logging.warning(f"⚠️ Duplicate Key: `{key}` found in {', '.join(files)}")
            print(f"⚠️ Duplicate Key: `{key}` found in {', '.join(files)}")

    logging.info("✅ Config redundancy check completed.")

if __name__ == "__main__":
    configs = load_configs()
    check_redundancy(configs)
    print(f"📜 Log file saved at: {LOG_FILE}")
