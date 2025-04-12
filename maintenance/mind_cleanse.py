import json
import boto3
import io

S3_BUCKET = "swylie-astra"
MIND_FILE_KEY = "mind_file.json"
BACKUP_KEY = "mind_file_backup.json"

s3 = boto3.client("s3")

def download():
    print("📥 Downloading original mind file...")
    response = s3.get_object(Bucket=S3_BUCKET, Key=MIND_FILE_KEY)
    return json.load(io.BytesIO(response["Body"].read()))

def upload(data, key):
    print(f"💾 Uploading to {key}...")
    json_bytes = json.dumps(data, indent=2).encode("utf-8")
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json_bytes)
    print("✅ Upload complete.")

def clean(data):
    def dedupe(entries, label):
        seen, out = set(), []
        for i, e in enumerate(entries):
            if not isinstance(e, str):
                print(f"❌ [Invalid {label}] [{i}] Non-string entry: {e}")
                continue
            norm = e.strip().lower()
            if norm not in seen and 10 < len(e) < 2000:
                seen.add(norm)
                out.append(e)
        return out

    data["self_reflections"] = dedupe(data.get("self_reflections", []), "reflection")
    data["self_questions"] = dedupe(data.get("self_questions", []), "question")
    data["stored_knowledge"] = dedupe(data.get("stored_knowledge", []), "knowledge")
    return data

def main():
    original = download()
    upload(original, BACKUP_KEY)

    cleaned = clean(original)
    print("🧠 Cleanup Preview:")
    print("Reflections:", len(cleaned.get("self_reflections", [])))
    print("Questions:", len(cleaned.get("self_questions", [])))
    print("Knowledge:", len(cleaned.get("stored_knowledge", [])))

    confirm = input("🚨 Overwrite original mind file with cleaned version? (yes/no): ")
    if confirm.strip().lower() == "yes":
        upload(cleaned, MIND_FILE_KEY)
    else:
        print("❌ Cancelled.")

if __name__ == "__main__":
    main()
