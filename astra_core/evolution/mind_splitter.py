"""
mind_splitter.py

Stubbed modular splitter that breaks mind_file.json into modular components
based on mind_manifest.json. Simulates upload to S3, and prepares for a
future phase where Astra can upload, validate, and self-refactor safely.
Also includes modular mind loader for compatibility with legacy callers.
"""

import json
import os
import boto3
from astra_core.config_loader import load_config
from astra_interfaces.influence import load_mind as load_legacy_mind  # avoid circular import by aliasing

# Constants
PROJECT_ROOT = os.path.expanduser("~/astra_reflections")
MIND_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "mind_manifest.json")
DRY_RUN_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "modular_mind_dry_run")
os.makedirs(DRY_RUN_OUTPUT_DIR, exist_ok=True)

# Load general config to fetch bucket name
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")

# Initialize S3 client (but dry-run only for now)
s3 = boto3.client("s3")
DRY_RUN = True  # ✅ Change this to False for real upload (in future)

def run_dream_split():
    with open(MIND_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    modules = manifest.get("modules", {})
    mind_data = load_legacy_mind()  # ✅ Temporarily use flat loader for valid data split

    print("\n🌙 Dream Phase: Splitting mind based on manifest...")

    for key, s3_path in modules.items():
        content = mind_data.get(key)
        if content is None:
            print(f"[mind_splitter.py] ⚠️ Skipping '{key}' — no data present in mind_file.json")
            continue

        # Save locally
        local_path = os.path.join(DRY_RUN_OUTPUT_DIR, f"{key}.json")
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        count = len(content) if isinstance(content, list) else len(content.keys())

        if DRY_RUN:
            print(f"[mind_splitter.py] 📤 Would upload '{key}.json' to {s3_path} — {count} entries")
        else:
            bucket, key_path = parse_s3_path(s3_path)
            try:
                s3.put_object(Bucket=bucket, Key=key_path, Body=json.dumps(content).encode("utf-8"))
                print(f"✅ Uploaded '{key}.json' to {s3_path}")
            except Exception as e:
                print(f"🚨 Upload failed for '{key}': {e}")

    print(f"\n✅ Dream refactor complete. Output written to: {DRY_RUN_OUTPUT_DIR}")

def parse_s3_path(s3_uri):
    """Split s3://bucket/key into (bucket, key)"""
    path = s3_uri.replace("s3://", "")
    parts = path.split("/", 1)
    return parts[0], parts[1]

def load_modular_mind(modules=None):
    """Load modular components based on manifest and merge into a flat mind_data dict"""
    if modules is None:
        with open(MIND_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            modules = manifest.get("modules", {})

    mind_data = {}
    for key, s3_path in modules.items():
        bucket, key_path = parse_s3_path(s3_path)
        try:
            response = s3.get_object(Bucket=bucket, Key=key_path)
            content = json.load(response["Body"])
            mind_data[key] = content
        except Exception as e:
            print(f"⚠️ Failed to load '{key}' from {s3_path}: {e}")
            mind_data[key] = [] if key != "emotional_state" else {}

    return mind_data

if __name__ == "__main__":
    run_dream_split()