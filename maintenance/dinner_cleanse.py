import json
import boto3

BLOCKED_TERMS = {
    "the", "a", "an", "and", "or", "in", "on", "with", "to", "from", "at", "by", 
    "for", "of", "this", "that", "these", "those", "english", "however", 
    "nevertheless", "historically", "history", "spinning"
}

def cleanse_dinner_journal(s3_bucket: str, s3_key: str, dry_run: bool = True):
    s3 = boto3.client("s3")
    print(f"📥 Loading journal from s3://{s3_bucket}/{s3_key}")

    try:
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        journal = json.load(response["Body"])
    except Exception as e:
        print(f"❌ Failed to load journal: {e}")
        return

    print(f"📊 Original entries: {len(journal)}")

    cleaned, removed = [], []
    for entry in journal:
        term = (entry.get("content") or entry.get("trigger") or "").lower()
        if any(bad in term for bad in BLOCKED_TERMS):
            removed.append(entry)
        else:
            cleaned.append(entry)

    print(f"🧹 Removed {len(removed)} junk entries")
    print(f"✅ Remaining entries: {len(cleaned)}")

    if not dry_run:
        try:
            s3.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=json.dumps(cleaned, indent=2).encode("utf-8")
            )
            print("📤 Cleaned journal uploaded.")
        except Exception as e:
            print(f"❌ Failed to upload cleaned journal: {e}")
    else:
        print("💡 Dry run mode enabled — no changes saved.")

    return cleaned, removed


if __name__ == "__main__":
    cleanse_dinner_journal("swylie-astra", "dinner_journal.json", dry_run=False)
