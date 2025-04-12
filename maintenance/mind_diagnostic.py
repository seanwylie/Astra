import os
import json
import boto3
import io
from fuzzywuzzy import fuzz


# Configure your AWS S3 access
S3_BUCKET = "swylie-astra"
MIND_FILE_KEY = "mind_file.json"

s3 = boto3.client("s3")

def download_mind_file():
    try:
        print("🔍 Downloading mind file from S3...")
        response = s3.get_object(Bucket=S3_BUCKET, Key=MIND_FILE_KEY)
        return json.load(io.BytesIO(response["Body"].read()))
    except Exception as e:
        print(f"❌ Failed to download or parse mind file: {e}")
        return None

def dry_run_validate_mind(mind_data):
    print("🧠 Starting dry run validation...")
    
    def check_duplicates(entries, label):
        unique = set()
        dups = set()
        for e in entries:
            norm = e.strip().lower()
            if norm in unique:
                dups.add(norm)
            else:
                unique.add(norm)
        if dups:
            print(f"⚠️ Duplicate {label} detected: {len(dups)}")
            for d in list(dups)[:3]:
                print(f"   - {d[:80]}...")
        else:
            print(f"✅ No duplicate {label} detected.")

    def check_invalid(entries, label):
        issues = []
        for i, e in enumerate(entries):
            if not isinstance(e, str):
                issues.append((i, "Non-string"))
            elif len(e.strip()) < 10:
                issues.append((i, "Too short"))
            elif len(e) > 2000:
                issues.append((i, "Too long"))
        if issues:
            print(f"⚠️ Invalid {label} entries: {len(issues)}")
            for idx, reason in issues[:3]:
                print(f"   - {label}[{idx}] → {reason}: {str(entries[idx])[:80]}")
        else:
            print(f"✅ All {label} entries passed structural checks.")

    if not isinstance(mind_data, dict):
        print("❌ Mind data is not a dictionary.")
        return

    reflections = mind_data.get("self_reflections", [])
    questions = mind_data.get("self_questions", [])
    knowledge = mind_data.get("stored_knowledge", [])

    print(f"🧾 Counts → Reflections: {len(reflections)}, Questions: {len(questions)}, Knowledge: {len(knowledge)}")

    check_duplicates(reflections, "reflections")
    check_invalid(reflections, "reflections")

    check_duplicates(questions, "questions")
    check_invalid(questions, "questions")

    check_duplicates(knowledge, "knowledge")
    check_invalid(knowledge, "knowledge")



def deduplicate_and_clean(entries, label="entry", min_length=25, dedupe_threshold=90):
    seen = []
    cleaned = []
    dropped = []

    for e in entries:
        if not isinstance(e, str):
            continue
        stripped = e.strip()
        if len(stripped) < min_length or len(stripped) > 2000:
            dropped.append((stripped[:100], "Invalid length"))
            continue
        if any(fuzz.ratio(stripped[:400], s[:400]) > dedupe_threshold for s in seen):
            dropped.append((stripped[:100], "Duplicate"))
            continue
        seen.append(stripped)
        cleaned.append(stripped)

    print(f"\n🧹 {label.title()} Cleanup Preview:")
    print(f"   • Original: {len(entries)} → Cleaned: {len(cleaned)}")
    print(f"   • Dropped: {len(dropped)}")
    for sample, reason in dropped[:3]:
        print(f"     🔻 {reason}: {sample}")

    return cleaned

def preview_cleaned_mind(mind_data):
    print("\n🚧 Previewing cleaned version of Astra's mind...")

    cleaned = {
        "self_reflections": deduplicate_and_clean(mind_data.get("self_reflections", []), "reflections"),
        "self_questions": deduplicate_and_clean(mind_data.get("self_questions", []), "questions", min_length=10),
        "stored_knowledge": deduplicate_and_clean(mind_data.get("stored_knowledge", []), "knowledge", min_length=25),
    }

    print("\n✅ Cleanup complete (dry run only).")
    print(f"🧠 Final preview counts → Reflections: {len(cleaned['self_reflections'])}, "
          f"Questions: {len(cleaned['self_questions'])}, Knowledge: {len(cleaned['stored_knowledge'])}")


if __name__ == "__main__":
    mind = download_mind_file()
    if mind:
        dry_run_validate_mind(mind)
        preview_cleaned_mind(mind)


