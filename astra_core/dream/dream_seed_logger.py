import json
import io
import time
import boto3
from datetime import datetime
from utils.time_utils import iso_now


S3_BUCKET = "swylie-astra"
DREAM_SEED_KEY = "dream_seeds.json"
s3 = boto3.client("s3")


def now():
    return iso_now()


def log_dream_seed(content, source="playtime"):
    """Append a new dream seed to S3."""
    seeds = load_dream_seeds()
    if content not in [s["content"] for s in seeds]:
        seeds.append({
            "content": content,
            "source": source,
            "timestamp": now()
        })
        save_dream_seeds(seeds)
        print(f"🌱 Logged dream seed from {source}.")
    else:
        print("⚠️ Duplicate dream seed skipped.")


def load_dream_seeds():
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=DREAM_SEED_KEY)
        return json.load(io.BytesIO(response["Body"].read()))
    except s3.exceptions.NoSuchKey:
        print("📄 No dream seeds yet. Starting fresh.")
        return []
    except Exception as e:
        print(f"⚠️ Failed to load dream seeds: {e}")
        return []


def save_dream_seeds(data):
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=DREAM_SEED_KEY,
            Body=json.dumps(data, indent=2).encode("utf-8")
        )
        print("✅ Dream seeds saved.")
    except Exception as e:
        print(f"❌ Failed to save dream seeds: {e}")


def remove_dream_seed(content):
    seeds = load_dream_seeds()
    filtered = [s for s in seeds if s["content"] != content]
    if len(filtered) < len(seeds):
        save_dream_seeds(filtered)
        print("🧹 Dream seed removed after reflection.")
    else:
        print("⚠️ Seed not found to remove.")
