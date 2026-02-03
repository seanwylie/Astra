import json
import io
import time
import boto3
from datetime import datetime

from app.logging_config import get_logger

logger = get_logger(__name__)


def iso_now():
    return datetime.now().isoformat()


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
        logger.info("Logged dream seed from %s.", source)
    else:
        logger.debug("Duplicate dream seed skipped.")


def load_dream_seeds():
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=DREAM_SEED_KEY)
        return json.load(io.BytesIO(response["Body"].read()))
    except s3.exceptions.NoSuchKey:
        logger.debug("No dream seeds yet. Starting fresh.")
        return []
    except Exception as e:
        logger.warning("Failed to load dream seeds: %s", e)
        return []


def save_dream_seeds(data):
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=DREAM_SEED_KEY,
            Body=json.dumps(data, indent=2).encode("utf-8")
        )
        logger.debug("Dream seeds saved.")
    except Exception as e:
        logger.warning("Failed to save dream seeds: %s", e)


def remove_dream_seed(content):
    seeds = load_dream_seeds()
    filtered = [s for s in seeds if s["content"] != content]
    if len(filtered) < len(seeds):
        save_dream_seeds(filtered)
        logger.info("Dream seed removed after reflection.")
    else:
        logger.debug("Seed not found to remove.")
