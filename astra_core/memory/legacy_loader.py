import boto3
import io
import json
from astra_core.config_loader import load_config

# Load config
config = load_config("general_config")
S3_BUCKET_NAME = config.get("s3_bucket", "swylie-astra")
MIND_FILE_JSON = config.get("mind_file", "mind_file.json")

# Initialize S3 client
s3 = boto3.client("s3")

def load_legacy_mind():
    """Loads flat mind_file.json from S3."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=MIND_FILE_JSON)
        mind_data = json.load(io.BytesIO(response["Body"].read()))
        print(f"📝 [LEGACY] Loaded {len(mind_data.get('stored_knowledge', []))} knowledge entries.")
        return mind_data
    except Exception as e:
        print(f"⚠️ Failed to load legacy mind_file.json: {e}")
        return None
