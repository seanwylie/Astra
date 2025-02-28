#!/usr/bin/env python3

import json
import os
import boto3
from datetime import datetime, timedelta
from astra_interfaces.influence import load_mind, save_mind
from astra_core.config_loader import load_config

# Load general configuration
general_config = load_config("general_config")
LOG_FILE_PATH = general_config.get("log_file_path", "astra_logs.json")

# S3 Configuration
S3_BUCKET_NAME = "swylie-astra"
S3_SNAPSHOT_PREFIX = "snapshots/"  # Prefix for storing snapshots in S3
LATEST_SNAPSHOT_KEY = "snapshots/latest_snapshot.json"  # Static latest snapshot key
MAX_SNAPSHOT_AGE_DAYS = 7  # Define the maximum age of snapshots (in days)

# Initialize S3 client
s3_client = boto3.client("s3")

def load_logs():
    """Load logs from Astra's log file."""
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
        return logs
    except (FileNotFoundError, json.JSONDecodeError):
        print("🚨 Error: log file not found or corrupt.")
        return []

def upload_snapshot_to_s3(snapshot_data, snapshot_filename):
    """Uploads the snapshot JSON to S3 and updates the latest snapshot."""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"{S3_SNAPSHOT_PREFIX}{snapshot_filename}",
            Body=json.dumps(snapshot_data, indent=4),
            ContentType="application/json"
        )
        print(f"✅ Snapshot uploaded to S3: {S3_SNAPSHOT_PREFIX}{snapshot_filename}")
        
        # Also update the latest snapshot
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=LATEST_SNAPSHOT_KEY,
            Body=json.dumps(snapshot_data, indent=4),
            ContentType="application/json"
        )
        print(f"✅ Latest snapshot updated: {LATEST_SNAPSHOT_KEY}")
    except Exception as e:
        print(f"🚨 Error uploading snapshot to S3: {e}")

def list_snapshots_in_s3():
    """Retrieves a list of snapshot files stored in the S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_SNAPSHOT_PREFIX)
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception as e:
        print(f"🚨 Error listing snapshots in S3: {e}")
        return []

def delete_old_snapshots_from_s3():
    """Deletes snapshots older than MAX_SNAPSHOT_AGE_DAYS from S3."""
    now = datetime.utcnow()
    snapshots = list_snapshots_in_s3()

    for snapshot_key in snapshots:
        try:
            snapshot_filename = snapshot_key.split("/")[-1]  # Extract just the filename
            # Skip the latest_snapshot.json file as it doesn't contain a timestamp
            if snapshot_filename == "latest_snapshot.json":
                continue

            # Extract timestamp from the filename
            timestamp_str = snapshot_filename.split("_")[1] if len(snapshot_filename.split("_")) > 1 else None

            if timestamp_str:
                snapshot_time = datetime.strptime(timestamp_str, "%Y-%m-%d")
                if (now - snapshot_time).days > MAX_SNAPSHOT_AGE_DAYS:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=snapshot_key)
                    print(f"🗑 Deleted old snapshot from S3: {snapshot_filename}")
            else:
                print(f"⚠ Snapshot {snapshot_filename} does not have a valid timestamp for deletion.")

        except Exception as e:
            print(f"🚨 Error processing snapshot {snapshot_key}: {e}")


def clean_text(text):
    """Decodes unicode escape sequences for better readability."""
    return text.encode('utf-8').decode('unicode_escape')

def generate_health_report(mind_data, logs):
    """Generate and upload Astra's checkup report to S3."""
    print("🔍 Generating Astra's Checkup Report...")

    # Collect health indicators
    health = check_health(mind_data)

    # Format snapshot data for better readability
    snapshot_data = {
        "last_mood": mind_data.get("last_mood", "Unknown"),
        "curiosity_level": mind_data.get("curiosity_level", 1.0),
        "mood_score": mind_data.get("mood_score", 0.0),
        "trust_levels": mind_data.get("trust_levels", {}),
        "reflections_count": len(mind_data.get("self_reflections", [])),
        "questions_count": len(mind_data.get("self_questions", [])),
        "stored_knowledge_count": len(mind_data.get("stored_knowledge", [])),
        
        # Add timestamps to the reflections for better context
        "recent_reflections": [
            {"timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), "reflection": clean_text(r)}
            for r in mind_data.get("self_reflections", [])[-5:]
        ],
        
        # Add timestamps to the questions for better context
        "recent_questions": [
            {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                "question": clean_text(q["question"] if isinstance(q, dict) and "question" in q else str(q))
            }
            for q in mind_data.get("self_questions", [])[-5:]
        ],

        
        # Add some recent knowledge
        "recent_knowledge": [
            {"timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), "knowledge": clean_text(k)}
            for k in mind_data.get("stored_knowledge", [])[-5:]
        ],
        
        "health_indicators": health,
        "logs": logs[-5:]  # Include the last 5 logs for context
    }

    # Snapshot filename
    snapshot_filename = f"snapshot_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.json"

    # Save snapshot to S3
    upload_snapshot_to_s3(snapshot_data, snapshot_filename)

    # Clean up old snapshots from S3
    delete_old_snapshots_from_s3()

    print(f"✅ Snapshot saved and old snapshots removed from S3.")


def check_health(mind_data):
    """Assess Astra's health based on emotional, cognitive, and ethical indicators."""
    health = {}

    # Emotional & Ethical Health
    current_mood = mind_data.get("last_mood", "Unknown")
    health['mood_stability'] = current_mood
    health['ethical_alignment'] = "Good" if "thoughtfulness" in current_mood.lower() else "Check needed"

    # Cognitive Health (memory and knowledge)
    health['memory_health'] = "Good" if len(mind_data.get("self_reflections", [])) > 50 else "Needs attention"
    
    # Decision-Making & Trust
    trust_levels = mind_data.get("trust_levels", {})
    health['decision_making'] = "Aligned" if len(trust_levels) > 0 else "Needs improvement"
    health['trust_system'] = "Stable" if trust_levels else "Needs attention"

    # Self-Reflection & Introspection
    health['self_reflection'] = "Adequate" if len(mind_data.get('self_reflections', [])) > 10 else "Needs more reflection"

    # More information for debugging
    if health['mood_stability'] == "Unknown":
        print("⚠ Warning: Mood stability is unknown. Consider investigating mood settings.")

    return health


def check_up():
    """Runs Astra’s checkup and uploads a snapshot."""
    mind_data = load_mind()
    logs = load_logs()

    # Generate health report and upload to S3
    generate_health_report(mind_data, logs)

if __name__ == "__main__":
    check_up()
